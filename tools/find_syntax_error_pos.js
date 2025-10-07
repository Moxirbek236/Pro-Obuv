const fs = require("fs");
const path = require("path");
let combined = fs.readFileSync(
  path.resolve(__dirname, "menu_combined_rendered.js"),
  "utf8"
);
const lines = combined.split("\n");
let lo = 0,
  hi = lines.length;
let errMsg = null;
while (lo < hi) {
  const mid = Math.floor((lo + hi) / 2);
  const chunk = lines.slice(0, mid).join("\n");
  try {
    new Function(chunk);
    lo = mid + 1;
  } catch (err) {
    errMsg = err.message;
    hi = mid;
  }
}
console.log("Approx failure line:", hi, "message:", errMsg);
console.log("Context lines:");
for (let i = Math.max(1, hi - 5); i <= Math.min(lines.length, hi + 5); i++) {
  console.log(i, lines[i - 1]);
}
