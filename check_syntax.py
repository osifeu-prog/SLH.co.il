import ast
with open('bot.py', 'r', encoding='utf-8') as f:
    ast.parse(f.read())
print('Syntax OK')
