from level4_data_mgt import app

def main(json_obj):
    start_pos_lst = json_obj.get('start_position')
    end_pos_lst = json_obj.get('end_position')
    protein_change_lst = json_obj.get('protein_change')
    category_lst = json_obj.get('variant_classification')

    app.logger.debug("Start Postion List: %s" % str(start_pos_lst))
    app.logger.debug("End Postion List: %s" % str(end_pos_lst))
    # start_pos_lst and end_pos_lst may be integer or string
    coord = [str(start_pos) if int(start_pos) - int(end_pos) == 0 else '-'.join((str(start_pos), str(end_pos)))
                for start_pos, end_pos in zip(start_pos_lst, end_pos_lst)]
    mut_info = []
    for item in set(coord):
        indexes = get_indexes(item, coord)
        categories = get_items(category_lst, indexes)

        for category in set(categories):
            mut_info.append({
                "coord": item,
                "category": category,
                "value": categories.count(category)
            })
    new_json_obj = {
        "data": mut_info,
        "metadata": {
            "max_coord": max(start_pos_lst + end_pos_lst),
            "min_coord": min(start_pos_lst + end_pos_lst)
        },
        "message": json_obj.get('message')
    }
    return new_json_obj

def get_indexes(pattern, lst):
    return [idx for idx, item in enumerate(lst) if item  == pattern]

def get_items(lst, idx_lst):
    return [lst[idx] for idx in idx_lst]