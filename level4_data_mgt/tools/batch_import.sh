#!/bin/bash

txt2json2db() {
    while IFS="," read project_name subproject_name exp_file
    do
        if [ "$project_name" == "project_name" ] || [ -z "$project_name" ];then
            continue
        else
            echo "project_name: $project_name"
            echo "subproject_name: $subproject_name"
            echo "exp_file: $exp_file"
            if [ -z `which python3` ];then
                echo "请安装Python3"
                exit 1
            else
                echo "生成JSON文件..."
                python "$program_dir"/import_data.py --project-name "$project_name" --subproject-name "$subproject_name" --dbtype "$collection" \
                                                     --jsontype "$data_type" --output-file "$data_dir/output.json" "$data_dir"/"$exp_file"
                if [ "$?" == 0 ];then
                    echo "导入数据库: $exp_file"
                    mongoimport -d "$database" -c "$collection" --host $host:$port "$data_dir"/output.json
                    rm "$data_dir"/output.json
                    if [ "$?" != 0 ];then
                        echo "无法导入数据，请查看MongoDB日志文件"
                        exit
                    fi
                else
                    exit 
                fi
            fi
        fi
    done < "$projects_file"
}

show_help(){
cat << EOF
usage: $(echo $0) [-t <DATA_TYPE>] [-d <DATABASE>] [-c <COLLECTION>] [-H <HOST>] [-p <PORT>] PROJECTS_FILE
       -t DATA_TYPE: data_type.
       -d DATABASE: database.
       -c COLLECTION: collection name
       -H HOST
       -p PORT
       PROJECTS_FILE: projects file.
Examples:
        # Host: 10.157.72.40
        # Port: 1998
        # Database: nordata_server
        # Collection: gene_expr
        # DataType: gene_exprs (import_data.py need this argument)
        bash batch_import.sh -t "gene_exprs" -d "nordata_server" -c "gene_expr" -H 10.157.72.40 -p 1998 ~/Downloads/level4_data/Tumor_normal_start_information.txt
        bash batch_import.sh -t "gene_exprs" -d "test" -c "test" ~/Downloads/level4_data/Tumor_normal_start_information.txt
Details:
        projects file header:
            project_name subproject_name exp_file
EOF
}

while getopts ":p:t:H:c:hd:" arg
do
    case "$arg" in
        "t")
            data_type="$OPTARG"
            ;;
        "d")
            database="$OPTARG"
            ;;
        "c")
            collection="$OPTARG"
            ;;
        "p")
            port="$OPTARG"
            ;;
        "H")
            host="$OPTARG"
            ;;
        "?")
            echo "Unkown option: $OPTARG"
            exit 1
            ;;
        ":")
            echo "No argument value for option $OPTARG"
            ;;
        h)
            show_help
            exit 0
            ;;
        \?)
            echo "Unknown error while processing options"
            show_help
            exit 1
            ;;
    esac
done

program_dir=$(cd "$(dirname "$0")"; pwd)
shift $(($OPTIND - 1))
if [ $# -eq 0 ]; then
    show_help
fi

if [ -z "$data_type" ]; then
    echo "You must specify DATA_TYPE with -t option"
    exit
fi

if [ -z "$database" ]; then
    echo "You must specify DATABASE with -d option"
    exit
fi

if [ -z "$collection" ]; then
    echo "You must specify COLLECTION with -c option"
    exit
fi

if [ -z "$host" ]; then
    host=127.0.0.1
fi

if [ -z "$port" ]; then
    port=27017
fi

if [ "$#" == 1 ];then
    projects_file=$@
    if [ ! -f "$projects_file" ];then
        echo "No such file: $projects_file"
        exit
    fi
    echo "读取$projects_file"
    # 解决while...read无法读取最后一行的问题
    echo '' >> "$projects_file"
    data_dir=$(cd "$(dirname "$projects_file")"; pwd)
    txt2json2db
elif [ "$#" == 0 ];then
    echo "必须输入参数：PROJECTS_FILE"
    exit
else
    echo "未知参数[$@]"
    exit
fi