import subprocess

with open('frontend/rh/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

parts = content.split('<script>')
header = parts[0]
script_and_after = parts[1].split('</script>')
script = script_and_after[0]
footer = script_and_after[1]

# Remplacer les échappements incorrects \` et \${
fixed_script = script.replace('\\`', '`').replace('\\${', '${')

fixed_content = header + '<script>' + fixed_script + '</script>' + footer

with open('frontend/rh/index.html', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

with open('temp_script.js', 'w', encoding='utf-8') as f:
    f.write(fixed_script)

res = subprocess.run(['node', '--check', 'temp_script.js'], capture_output=True, text=True)
print('SYNTAX CHECK EXIT CODE:', res.returncode)
if res.returncode != 0:
    print('ERRORS:\n', res.stderr)
else:
    print('SUCCESS: ZERO SYNTAX ERRORS IN JS!')
