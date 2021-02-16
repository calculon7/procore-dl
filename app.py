from procore import Procore

p = Procore()
p.username = 'REDACTED'
p.password = 'REDACTED'

p.login()

companies = p.get_companies()
suffolk = next(filter(lambda x: x['id'] == 4799, companies))

projects = p.get_projects(suffolk['id'])
project = next(filter(lambda x: x['id'] == 924722, projects))

folders = p.get_folders(project['id'])

pass
