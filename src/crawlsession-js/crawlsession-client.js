/**
 * Crawl API Session Example
 * 
 * This example demonstrates using the Crawl API with sessions to:
 * 1. Create a session and crawl the Bulma.io homepage
 * 2. Parse the HTML to find stylesheet links
 * 3. Crawl each stylesheet within the same session
 * 4. Process the results
 */

const fetch = require('node-fetch');
const zlib = require('zlib');
const util = require('util');

// Configuration
//const API_KEY = 'test-a5e2a409065c590c20d1d8f80bc9329d'; // Local test API key
//const BASE_URL = 'http://localhost:8080';
const API_KEY = 'crawl-dev-aQR9E7rq94vhaZAU0zHH';
const BASE_URL = 'https://cdg002.dev.uprock.com';
//const INITIAL_URL = 'https://bulma.io/';
const INITIAL_URL = 'https://ipinfo.io/json';
//const INITIAL_URL = 'https://www.ebay.ca/';


// Modern Chrome browser user agent
const CHROME_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

// Create a new crawl session
async function createSession(durationSeconds = 300) {
  console.log("Creating a new crawl session...");
  
  const sessionRequest = {
    duration_seconds: durationSeconds,
    // Optional placement constraints could be added here
  };
  
  const response = await fetch(`${BASE_URL}/crawl/v1/session/new`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(sessionRequest)
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    console.error(`Failed to create session: ${response.status} - ${errorText}`);
    return null;
  }
  
  const data = await response.json();
  console.log("Session created successfully:", JSON.stringify(data, null, 2));
  
  return data.session_id;
}

// Close an existing session
async function closeSession(sessionId) {
  if (!sessionId) {
    console.warn("No session ID provided to close");
    return false;
  }
  
  console.log(`Closing session ${sessionId}...`);
  
  try {
    const response = await fetch(`${BASE_URL}/crawl/v1/session/${sessionId}/close`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Failed to close session: ${response.status} - ${errorText}`);
      return false;
    }
    
    console.log(`Session ${sessionId} closed successfully`);
    return true;
  } catch (error) {
    console.error(`Error closing session: ${error.message}`);
    return false;
  }
}

async function main() {
  try {
    console.log('=== Crawl Session Example ===');
    
    // Parse command line arguments
    const useSession = true;//false;//!process.argv.includes('--no-session');
    console.log(`Running with ${useSession ? 'session support' : 'NO session support'}`);
    
    let sessionId = null;
    
    // Step 1: Create a session first (if not disabled)
    if (useSession) {
      console.log("\n1. Creating a crawl session");
      sessionId = await createSession(300); // 5 minute session
      
      if (!sessionId) {
        console.error("Failed to create session. Make sure the server database migrations have been run.");
        console.error("Continuing without session support...");
      } else {
        console.log(`Session created with ID: ${sessionId}`);
      }
    } else {
      console.log("\n1. Session creation skipped (--no-session flag provided)");
    }
    
    // Step 2: Submit initial crawl job for Bulma.io homepage with the session ID
    console.log(`\n2. Crawling initial URL: ${INITIAL_URL}`);
    const initialJob = await submitCrawlJob(INITIAL_URL, sessionId);
    console.log(`Initial job submitted with ID: ${initialJob.jobId}`);
    
    // Step 3: Poll for initial job completion
    console.log('\n3. Waiting for initial crawl to complete...');
    const initialResult = await pollJobStatus(initialJob.jobId);
    
    if (initialResult.status === 'completed') {
      console.log('Initial crawl completed successfully');
      
      // Step 4: Download and parse the HTML content
      console.log('\n4. Downloading and parsing HTML content...');
      const htmlContent = await downloadJobContent(initialJob.jobId);
      console.log(`Downloaded ${htmlContent.length} bytes of HTML content`);
      

      console.log('HTML Content:', htmlContent.toString());

      // Extract stylesheet links
      const stylesheetLinks = extractStylesheetLinks(htmlContent.toString());
      console.log(`Found ${stylesheetLinks.length} stylesheet links:`);
      stylesheetLinks.forEach(link => console.log(`   - ${link}`));
      
      // Step 5: Crawl each stylesheet in sequence, using the same session
      console.log('\n5. Crawling stylesheets in session...');
      
      // Limit to first 3 stylesheets for the demo, to avoid potential issues
      const maxStylesheets = Math.min(3, stylesheetLinks.length);
      
      for (let i = 0; i < maxStylesheets; i++) {
        const stylesheetUrl = stylesheetLinks[i];
        console.log(`\n   Crawling stylesheet ${i+1}/${maxStylesheets}: ${stylesheetUrl}`);
        
        try {
          // Submit the job with session ID if we have one
          const stylesheetJob = await submitCrawlJob(stylesheetUrl, sessionId);
          
          // Update session ID if it was created/returned
          if (stylesheetJob.sessionId && !sessionId) {
            sessionId = stylesheetJob.sessionId;
            console.log(`   Session created with ID: ${sessionId}`);
          }
          
          // Wait for this stylesheet job to complete
          const stylesheetResult = await pollJobStatus(stylesheetJob.jobId);
          
          if (stylesheetResult.status === 'completed') {
            // Get stylesheet size
            const cssContent = await downloadJobContent(stylesheetJob.jobId);
            console.log(`   Downloaded ${cssContent.length} bytes of CSS content`);
            
            // Get some basic stats about the CSS
            const cssStats = getCSSStats(cssContent.toString());
            console.log(`   CSS Stats: ${cssStats.selectors} selectors, ${cssStats.rules} rules, ${cssStats.mediaQueries} media queries`);
          } else {
            console.log(`   Failed to download stylesheet: ${stylesheetResult.status}`);
          }
        } catch (error) {
          console.log(`   Error processing stylesheet ${stylesheetUrl}: ${error.message}`);
          // Continue with next stylesheet despite error
        }
      }
      
      // Step 6: Close the session
      if (sessionId) {
        console.log('\n6. Closing session...');
        await closeSession(sessionId);
        console.log(`   Processed ${stylesheetLinks.length} stylesheets in session ${sessionId}`);
      }
      
    } else {
      console.error(`Initial crawl failed with status: ${initialResult.status}`);
    }
    
  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Submit a crawl job with optional session ID
async function submitCrawlJob(url, sessionId = null) {
  console.log(`Submitting job for URL: ${url}${sessionId ? ` with session ID: ${sessionId}` : ''}`);
  
  const jobRequest = {
    url: url,
    method: 'GET',
    timeout_sec: 30,
    headers: {
      'User-Agent': [CHROME_USER_AGENT],
      'Accept': ['text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'],
      'Accept-Language': ['en-US,en;q=0.9'],
      'Accept-Encoding': ['gzip, deflate, br'],
      'Cache-Control': ['no-cache'],
      'Pragma': ['no-cache'],
      'Sec-Ch-Ua': ['"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'],
      'Sec-Ch-Ua-Mobile': ['?0'],
      'Sec-Ch-Ua-Platform': ['"Windows"'],
      'Sec-Fetch-Dest': ['document'],
      'Sec-Fetch-Mode': ['navigate'],
      'Sec-Fetch-Site': ['none'],
      'Sec-Fetch-User': ['?1'],
      'Upgrade-Insecure-Requests': ['1']
    }
  };
  
  // If we have a session ID, include it
  if (sessionId) {
    jobRequest.session_id = sessionId;
  }
  
  // For debugging
  console.log("Job request:", JSON.stringify({
    ...jobRequest,
    headers: "...(headers omitted)..."
  }, null, 2));
  
  const response = await fetch(`${BASE_URL}/crawl/v1/new`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(jobRequest)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to submit job: ${response.status} - ${errorText}`);
  }

  const data = await response.json();
  console.log("Job submission response:", JSON.stringify(data, null, 2));
  
  // Check for session issues
  if (sessionId && !data.session_id) {
    console.warn("WARNING: Session ID was provided but not returned in response.");
    console.warn("This may indicate the session feature is not enabled on the server.");
    console.warn("Make sure the server database migrations have been run.");
  }
  
  return {
    jobId: data.job_id,
    sessionId: data.session_id || null
  };
}

// Poll for job status until completed or failed
async function pollJobStatus(jobId) {
  let completed = false;
  let status = null;
  
  while (!completed) {
    const response = await fetch(`${BASE_URL}/crawl/v1/status/${jobId}`, {
      headers: {
        'Authorization': `Bearer ${API_KEY}`
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to get job status: ${response.status} ${response.statusText}`);
    }

    status = await response.json();
    console.log(`   Job ${jobId} status: ${status.status}`);
    
    // Log session ID if present
    if (status.session_id) {
      console.log(`   Job has session ID: ${status.session_id}`);
    }

    // Check if job is completed or failed
    if (status.status === 'completed' || status.status === 'failed' || status.status === 'timeout') {
      completed = true;
    } else {
      // Wait 2 seconds before polling again
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
  
  return status;
}

// Download job content
async function downloadJobContent(jobId) {
  const response = await fetch(`${BASE_URL}/crawl/v1/jobs/${jobId}/download`, {
    headers: {
      'Authorization': `Bearer ${API_KEY}`
    }
  });

  if (!response.ok) {
    throw new Error(`Failed to download job content: ${response.status} ${response.statusText}`);
  }

  // Get the content as a Buffer
  const buffer = await response.buffer();
  
  // Get job details to check content type and encoding
  const detailsResponse = await fetch(`${BASE_URL}/crawl/v1/jobs/${jobId}/detail`, {
    headers: {
      'Authorization': `Bearer ${API_KEY}`
    }
  });
  
  if (!detailsResponse.ok) {
    throw new Error(`Failed to get job details: ${detailsResponse.status} ${detailsResponse.statusText}`);
  }
  
  const details = await detailsResponse.json();
  
  const contentType = getHeaderValue(details.response_headers, 'content-type');
  const contentEncoding = getHeaderValue(details.response_headers, 'content-encoding');
  
  console.log(`Content Type: ${contentType || 'not specified'}`);
  console.log(`Content Encoding: ${contentEncoding || 'not specified'}`);
  
  let decompressedContent = buffer;
  
  // Try to decompress if we have encoding information
  if (contentEncoding) {
    try {
      if (contentEncoding.includes('gzip')) {
        console.log('Decompressing gzip content...');
        const gunzip = util.promisify(zlib.gunzip);
        decompressedContent = await gunzip(buffer);
      } else if (contentEncoding.includes('deflate')) {
        console.log('Decompressing deflate content...');
        const inflate = util.promisify(zlib.inflate);
        decompressedContent = await inflate(buffer);
      } else if (contentEncoding.includes('br')) {
        console.log('Decompressing brotli content...');
        const brotliDecompress = util.promisify(zlib.brotliDecompress);
        decompressedContent = await brotliDecompress(buffer);
      }
    } catch (error) {
      console.log(`Decompression error: ${error.message}`);
      // Continue with original buffer if decompression fails
      decompressedContent = buffer;
    }
  }
  
  // Validate HTML content if we're expecting HTML
  if (contentType && contentType.includes('text/html')) {
    const contentString = decompressedContent.toString();
    // Check for HTML doctype or tags
    if (!contentString.includes('<!doctype html') && 
        !contentString.includes('<html') && 
        !contentString.includes('<body')) {
      console.log('Warning: Content doesn\'t appear to be valid HTML after decompression.');
      console.log('First 100 bytes:', contentString.substring(0, 100));
      
      // If the response has content-encoding but failed to decompress properly,
      // we can try to request it without compression by disabling Accept-Encoding
      if (contentEncoding) {
        console.log('Attempting to fetch uncompressed content...');
        try {
          // Make another request without compression
          const uncompressedResponse = await fetch(`${BASE_URL}/crawl/v1/jobs/${jobId}/detail?include_body=true`, {
            headers: {
              'Authorization': `Bearer ${API_KEY}`,
              'Accept-Encoding': 'identity'
            }
          });
          
          if (uncompressedResponse.ok) {
            const detailWithBody = await uncompressedResponse.json();
            if (detailWithBody.body) {
              console.log('Successfully retrieved uncompressed content via detail API');
              return Buffer.from(detailWithBody.body);
            }
          }
        } catch (error) {
          console.log(`Error fetching uncompressed content: ${error.message}`);
        }
      }
    } else {
      console.log('Successfully decompressed HTML content');
    }
  }
  
  return decompressedContent;
}

// Helper function to get header value from response headers
function getHeaderValue(headers, name) {
  if (!headers) return null;
  
  // Find the header (case insensitive)
  const header = headers.find(h => 
    h.name.toLowerCase() === name.toLowerCase()
  );
  
  return header ? header.value : null;
}

// Function to extract stylesheet links from HTML
function extractStylesheetLinks(html) {
  const links = [];
  
  // Print a small sample of the HTML for debugging
  console.log("HTML Sample (first 200 chars):", html.substring(0, 200));
  
  // More comprehensive regex patterns to catch more variations of stylesheet links
  // This handles quotes/no quotes and various attribute orders
  const patterns = [
    // Standard stylesheet link
    /<link[^>]*rel=["']stylesheet["'][^>]*href=["']([^"']+)["'][^>]*>/gi,
    // Href first, then rel
    /<link[^>]*href=["']([^"']+)["'][^>]*rel=["']stylesheet["'][^>]*>/gi,
    // No quotes around attribute values
    /<link[^>]*rel=stylesheet[^>]*href=["']([^"']+)["'][^>]*>/gi,
    /<link[^>]*href=["']([^"']+)["'][^>]*rel=stylesheet[^>]*>/gi,
    // CSS in filename as fallback
    /<link[^>]*href=["']([^"']+\.css[^"']*)["'][^>]*>/gi
  ];
  
  // Try all patterns
  for (const pattern of patterns) {
    let match;
    while ((match = pattern.exec(html)) !== null) {
      try {
        // Convert relative URLs to absolute
        const href = new URL(match[1], INITIAL_URL).href;
        // Avoid duplicates
        if (!links.includes(href)) {
          links.push(href);
        }
      } catch (e) {
        console.log(`Error processing URL: ${match[1]}, Error: ${e.message}`);
      }
    }
  }
  
  // If still no links found, let's try a more direct CSS file search as fallback
  if (links.length === 0) {
    console.log("No stylesheet links found with standard patterns, trying fallback...");
    
    // Look for any .css references
    const cssUrlPattern = /["'](https?:\/\/[^"']+\.css[^"']*)["']/gi;
    let cssMatch;
    
    while ((cssMatch = cssUrlPattern.exec(html)) !== null) {
      const cssUrl = cssMatch[1];
      if (!links.includes(cssUrl)) {
        links.push(cssUrl);
      }
    }
    
    // Look for relative CSS paths
    const relCssPattern = /["'](\/[^"']*\.css[^"']*)["']/gi;
    while ((cssMatch = relCssPattern.exec(html)) !== null) {
      try {
        const href = new URL(cssMatch[1], INITIAL_URL).href;
        if (!links.includes(href)) {
          links.push(href);
        }
      } catch (e) {
        console.log(`Error processing relative URL: ${cssMatch[1]}, Error: ${e.message}`);
      }
    }
  }
  
  return links;
}

// Simple function to get basic CSS stats
function getCSSStats(css) {
  const selectorPattern = /[^{}]+\{/g;
  const rulePattern = /\{[^{}]*\}/g;
  const mediaQueryPattern = /@media[^{]+\{/g;
  
  // Count selectors, rules, and media queries
  const selectors = (css.match(selectorPattern) || []).length;
  const rules = (css.match(rulePattern) || []).length;
  const mediaQueries = (css.match(mediaQueryPattern) || []).length;
  
  return { selectors, rules, mediaQueries };
}

// Execute the example
main().catch(err => {
  console.error('Unhandled error:', err);
  process.exit(1);
});