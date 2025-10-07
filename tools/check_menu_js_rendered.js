const fs = require("fs");
const path = require("path");
const file = path.resolve(__dirname, "..", "templates", "menu.html");
let s = fs.readFileSync(file, "utf8");
// Remove Jinja block tags {% ... %}
s = s.replace(/\{\%[\s\S]*?\%\}/g, "");
// Replace Jinja expression tags {{ ... }} with 0 (safe placeholder)
s = s.replace(/\{\{[\s\S]*?\}\}/g, "0");
// Now extract script blocks
const scriptRe = /<script[^>]*>([\s\S]*?)<\/script>/gi;
let m;
let i = 0;
let combined = "";
while ((m = scriptRe.exec(s)) !== null) {
  i++;
  combined +=
    "\n// --- script block " +
    i +
    " start ---\n" +
    m[1] +
    "\n// --- script block " +
    i +
    " end ---\n";
}
console.log("Found", i, "script blocks, total length", combined.length);
try {
  new Function(combined);
  console.log("JS OK: no syntax errors detected.");
} catch (err) {
  console.error("JS SYNTAX ERROR:", err && err.message);
  if (err && err.stack) console.error(err.stack);
  fs.writeFileSync(
    path.resolve(__dirname, "menu_combined_rendered.js"),
    combined,
    "utf8"
  );
}
