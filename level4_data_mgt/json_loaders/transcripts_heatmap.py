from level4_data_mgt import app

def main(json_obj):
    data = json_obj.get('data')
    tissues = data.get('source_type_lst')
    transcript_ids = data.get("transcript_ensembl_id_lst")
    gene_ensembl_id = data.get("gene_ensembl_id_lst")[0]
    expr_value_lst = data.get("expr_value_lst")

    uniq_transcript_ids = sorted(set(transcript_ids))
    union_tissues = get_union(tissues, len(uniq_transcript_ids))
    app.logger.debug("组织类型列表: %s" % union_tissues)

    pos_expr_data = []
    for y_axis, transcript_id in enumerate(uniq_transcript_ids):
        first_idx, last_idx = get_index_range(transcript_ids, transcript_id)
        tissues_subset = tissues[first_idx:last_idx+1]

        app.logger.debug("转录本ID: %s" % transcript_id)
        app.logger.debug("区间范围: %s, %s" % (first_idx, last_idx+1))

        for x_axis, tissue in enumerate(union_tissues):
            expr_value = []
            if tissue in tissues_subset:
                index = get_index_range(tissues_subset, tissue, show_last_idx=False)
                length = len(tissues_subset)
                # 获取表达值的索引位置，last_idx指向相应transcript_id对应的区间最后一个元素位置
                # length: transcript_id对应的区间元素数目
                # index: 当前tissue在区间中的索引位置
                expr_value = expr_value_lst[last_idx+1 - length + index]
                pos_expr_data.append([y_axis, x_axis, expr_value])
            app.logger.debug("组织类型: %s" % tissue)
            app.logger.debug("y轴位置: %s" % y_axis)
            app.logger.debug("x轴位置: %s" % x_axis)
            app.logger.debug("表达值: %s" % expr_value)
            app.logger.debug("转录本: %s" % transcript_id)
    new_data = {
        "gene_ensembl_id": gene_ensembl_id,
        "data": pos_expr_data,
        "transcript_ids": uniq_transcript_ids,
        "tissues": union_tissues
    }
    json_obj['data'] = new_data
    return json_obj

def get_index_range(list1, str, show_last_idx=True):
    '''
    给定连续元素的列表，返回与指定str匹配的首末index
    '''
    flag = True
    for index, item in enumerate(list1):
        if item == str and flag:
            first_index = index
            flag = False
            continue
        if item == str:
            last_index = index
    if show_last_idx:
        return first_index, last_index
    else:
        return first_index

def get_union(list1, times):
    union_list = []
    for item in set(list1):
        if list1.count(item) == times:
            union_list.append(item)
    return sorted(union_list)
