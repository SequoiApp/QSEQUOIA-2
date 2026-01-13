#recup nom projet

args <- commandArgs(trailingOnly = TRUE)

if (length(args) == 0) {
    stop("No project name provided")
}

project_name <- args[1]

cat ("Nom du projet recupere :", project_name, "\n")