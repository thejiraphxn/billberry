const Snowflake = require('snowflake-id').Snowflake;

function isPretty(numstr) {
  if (numstr.startsWith('0')) return false;
  for (let i = 0; i < numstr.length - 2; i++) {
    if (numstr[i] === numstr[i+1] && numstr[i] === numstr[i+2]) return false;
  }
  for (let i = 0; i < numstr.length - 3; i++) {
    const s = numstr.slice(i, i+4);
    if ('0123456789'.includes(s) || '9876543210'.includes(s)) return false;
    try {
      const nums = Array.from(s).map(Number);
      // Ascending
      if (nums.join('') === [...Array(4).keys()].map(k => nums[0]+k).join('')) return false;
      // Descending
      if (nums.join('') === [...Array(4).keys()].map(k => nums[0]-k).join('')) return false;
    } catch {}
  }
  return true;
}

function generatePrettyId() {
  const gen = new Snowflake({ mid: 1, offset: (2020-1970)*31536000*1000 });
  while (true) {
    const id = gen.generate().toString();
    const numstr = id.slice(-10);
    if (isPretty(numstr)) return numstr;
  }
}

module.exports = { generatePrettyId };
