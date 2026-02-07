const fs = require("fs");
const path = require("path");
const file = path.resolve(__dirname, "..", "templates", "menu.html");
const s = fs.readFileSync(file, "utf8");
const scriptRe = /<script[^>]*>([\s\S]*?)<\/script>/gi;
let m;
let i = 0;
let combined = "";
while ((m = scriptRe.exec(s)) !== null) {
  i++;
  const code = m[1];
  combined +=
    `\n// --- script block ${i} start ---\n` +
    code +
    `\n// --- script block ${i} end ---\n`;
}
console.log("Found", i, "script blocks, total length", combined.length);
try {
  // Try to compile
  new Function(combined);
  console.log("JS OK: no syntax errors detected.");
} catch (err) {
  console.error("JS SYNTAX ERROR:", err && err.message);
  // Try to get line number by counting lines up to err.lineNumber if available
  if (err && err.stack) console.error(err.stack);
  // Save combined to tmp for manual inspection
  fs.writeFileSync(
    path.resolve(__dirname, "menu_combined.js"),
    combined,
    "utf8"
  );
}
