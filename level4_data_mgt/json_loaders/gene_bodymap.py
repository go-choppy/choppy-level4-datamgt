from level4_data_mgt import app

def main(json_obj):
    tissue_lst = ["Abdomen", "Adrenal_Gland", "Bladder", "Blood", "Brain", "Breast", "Cervix_Uteri", "Cholangio", "Colon", "Elbow", "Esophagus", "Eye", "Fallopian_Tube", "Forearm", "Heart", "Kidney", "Liver", "Lung", "Lymphonodus", "Muscle", "Neck", "Ovary", "Pancreas", "Prostate", "Salivary_Gland", "Small_Intestine", "Spleen", "Stomach", "Synovial", "Testis", "Thymus", "Thyroid", "Uterus", "Vagina"]
    expr_value_lst = [expr_value for expr_value in json_obj.get('expr_value_lst')]
    source_type = [item.replace(' ', '_') for item in json_obj.get('source_type')]
    subproject_name = json_obj.get('subproject_name')
    normal_tissue_idx = get_indexes('GTEx', subproject_name)
    tumor_tissue_idx = get_indexes('TCGA', subproject_name)

    normal_tissues = get_items(source_type, normal_tissue_idx)
    tumor_tissues = get_items(source_type, tumor_tissue_idx)
    nexpr_value_lst = get_items(expr_value_lst, normal_tissue_idx)
    texpr_value_lst = get_items(expr_value_lst, tumor_tissue_idx)

    normal_data = get_bodymap_data(normal_tissues, nexpr_value_lst, filter = tissue_lst)
    tumor_data = get_bodymap_data(tumor_tissues, texpr_value_lst, filter = tissue_lst)

    app.logger.debug("Normal Tissue Index: %s" % str(normal_tissue_idx))
    app.logger.debug("Tumor Tissue Index: %s" % str(tumor_tissue_idx))
    app.logger.debug("Normal Tissues: %s" % str(normal_tissues))
    app.logger.debug("Tumor Tissues: %s" % str(tumor_tissues))
    app.logger.debug("Normal Gene Bodymap: %s" % str(normal_data))
    app.logger.debug("Tumor Gene Bodymap: %s" % str(tumor_data))


    new_data = {
        "gene_ensembl_id": json_obj.get('gene_ensembl_id'),
        "normal_data": normal_data,
        "tumor_data": tumor_data
    }
    new_json_obj = {}
    new_json_obj['data'] = new_data
    new_json_obj['message'] = json_obj.get('message')
    new_json_obj['api_uri'] = '&'.join((json_obj.get('api_uri'), "loader=gene_bodymap"))
    return new_json_obj

def get_indexes(pattern, lst):
    return [idx for idx, item in enumerate(lst) if item  == pattern]

def get_items(lst, idx_lst):
    return [lst[idx] for idx in idx_lst]

def get_bodymap_data(tissues, expr_value_lst, filter=None):
    data = {}
    for tissue, expr_value in zip(tissues, expr_value_lst):
        if isinstance(filter, list) and tissue in filter or filter is None:
            data[tissue] = {
                'tissue_type': tissue,
                'tumor_types': [tissue],
                'exp_values': [expr_value]
            }

    return data