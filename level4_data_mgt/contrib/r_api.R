library(RCurl)
library(rjson)
library(httr)

.HTTPHOST <- "http://10.157.72.40"
.HTTPPORT <- 2000
.API <- "/genedata/api/v1/"
# v1末尾不能添加/，否则导致URL无法匹配
.RESTfulAPI <- "http://10.157.72.40:2000/genedata/api/v1"

set_api <- function(http_host, http_port, api){
  if(grepl("http://[0-9A-Za-z_/\\-]+[0-9a-zA-Z]$", http_host)){
    
    .HTTPHOST <<- http_host
  }else{
    stop("The format of http_host is wrong!")
  }

  if(grepl("[0-9]+", http_port) && (0 < http_port && http_port <= 65535)){
    .HTTPPORT <<- http_port
  }else{
    stop("The http_port must be integer, be greater than 0, and be less than 65535")
  }

  if(grepl("[0-9A-Za-z_/\\-]+", api)){
    .API <<- api
  }else{
    stop("The format of api is wrong!")
  }
  .RESTfulAPI <<- paste(paste(.HTTPHOST, .HTTPPORT, sep=":"), .API, "/", sep="/")
}

get_json_to_list <- function(url){
  content_json <- getURL(url)
  content_list <- fromJSON(content_json)
  return(content_list)
}

get_project_info <- function(project_name){
  url <- paste(.RESTfulAPI, "project", project_name, sep = "/")
  return(get_json_to_list(url)[["project_info"]])
}

get_exprs <- function(ensembl_id, project_name, tissue_type, species="human", id_type="gene"){
  BODY <- list(
    "project_name"=project_name,
    "tissue_type"=tissue_type,
    "species"=species
  )
  url <- paste(.RESTfulAPI, "gene", ensembl_id, sep = "/")
  rconnection <- GET(url, query=BODY, accept("*/*"), add_headers("Plotly-Client-Platform"="r"), verbose())
  stop_for_status(rconnection)
  gene_info <- content(rconnection)

  tumor_samples_name <- unlist(gene_info$gene_exprs$tumor_samples_name)
  tumor_expr_value <- data.frame(unlist(gene_info$gene_exprs$tumor_expr_value), row.names=tumor_samples_name)
  
  normal_samples_name <- unlist(gene_info$gene_exprs$normal_samples_name)
  normal_expr_value <- data.frame(unlist(gene_info$gene_exprs$normal_expr_value), row.names=normal_samples_name)
  
  project_name <- gene_info$gene_exprs$project_name
  species <- gene_info$gene_exprs$species
  tissue_type <- gene_info$gene_exprs$tissue_type
  
  info <- list(species=species, tissue_type=tissue_type, project_name=project_name)
  if(tolower(id_type) == "gene"){
    gene_ensembl_id <- gene_info$gene_exprs$gene_ensembl_id
    colnames(tumor_expr_value) <- gene_ensembl_id
    colnames(normal_expr_value) <- gene_ensembl_id
    info[['gene_ensembl_id']] <- gene_ensembl_id
  }else{
    transcript_ensembl_id <- gene_info$gene_exprs$transcript_ensembl_id
    colnames(tumor_expr_value) <- transcript_ensembl_id
    colnames(normal_expr_value) <- transcript_ensembl_id
    info[['transcript_ensembl_id']] <- transcript_ensembl_id
  }
  info[['normal_expr_value']] <- normal_expr_value
  info[['tumor_expr_value']] <- tumor_expr_value
  return(info)
}