import ast

def ind(n):
    return n*'    '


test_roles = ['admin', 'moderator', 'end_user', 'public']

with open('views.py','r') as f:
    data = f.read()
source_tree = ast.parse(data)


#Populate endpoints
endpoints = []
for node in source_tree.body:
    if isinstance(node,ast.FunctionDef):
        if len(node.decorator_list)>0:
            
            #Iterate Endpoints
            endpoint = {}
            endpoint['name'] = node.name
            for decorator in node.decorator_list:
                for arg in decorator.args:
                    if ':' in arg.value and '/' not in arg.value:
                        endpoint['permission'] = arg.value
                    else: 
                        endpoint['path'] = arg.value
                for keyword in decorator.keywords:
                    for method in keyword.value.elts:
                        endpoint['method'] = method.value.lower()
            endpoints.append(endpoint)

lines = []
for role in test_roles:
    length = len(role + ' tests')
    lines.append('#'*(length+4))
    lines.append('# ' + role + ' tests' + ' #')
    lines.append('#'*(length+4))
    lines.append('')
    for endpoint in endpoints:
        lines.append('def ' + 'test_' + role + '_' + endpoint['name'] + '(self):')
        lines.append('    ' + 'res = self.client().' + endpoint['method'] +
                "('" + endpoint['path'] + "')")
        lines.append('    pass')
        lines.append('')

for line in lines:
    print(line)
