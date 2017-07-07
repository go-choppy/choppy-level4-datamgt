import sys, os, json
BASEDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASEDIR)
print(sys.path)

from level4_data_mgt.models import get_expr_by_project, TranscriptExpr, GeneExpr

def main(project_name, subproject_name, ensembl_id, expr_cls, **kwargs):
    get_expr_by_project(project_name, subproject_name, ensembl_id, expr_cls, **kwargs)

if __name__ == '__main__':
    project_name = "ExpressionMean"
    subproject_name = "GTEx"
    ensembl_id = "ENSG00000164266"
    expr_cls = GeneExpr
    main(project_name, subproject_name, ensembl_id, expr_cls)