const decode = (str: string) => {
  const isBase64 = /^data:image\/[a-zA-Z]+;base64,/.test(str);
  try {
    if (isBase64) {
      return Buffer.from(str, 'base64').toString('utf-8');
    } else {
      return decodeURIComponent(str);
    }
  } catch {
    return str;
  }
};

export { decode };
