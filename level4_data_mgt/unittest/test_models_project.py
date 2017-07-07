import sys, os
BASEDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_TEMPLATES_DIR = BASEDIR + 'level4_data_mgt' + '/json_templates'
sys.path.append(BASEDIR)
print(sys.path)
from level4_data_mgt import JSON_TEMPLATES_DIR
from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('level4_data_mgt', 'json_templates'), trim_blocks = True, lstrip_blocks = True)
template = env.get_template('project_info.json.j2')

project = {
    'project_id': "12345",
    'analysis_pipeline': "analysis_pipeline",
    'created_date': "project.created_date",
    'data_file_md5': "project.data_file_md5",
    'data_file_name': "project.data_file_name",
    'data_type': "project.data_type", 
    'description': "project.description", 
    'import_data_program': "project.import_data_program", 
    'normalized': "project.normalized", 
    'normalized_method': "project.normalized_method", 
    'num_of_samples': "project.num_of_samples", 
    'project_name': "project.project_name", 
    'species': "project.species", 
    'src_project_id': "project.src_project_id", 
    'tissue_type': "project.tissue_type", 
    'tissue_t_full_name': "project.tissue_t_full_name", 
    'url': "project.url", 
    'version': "project.version" 
}

print(project['project_id'])

def test_get_project():
    return template.render(project=project, src_project = True, analysis_program = False)

if __name__ == '__main__':
    project = test_get_project()
    print(project)