# GCP

## 10. GCP

- Cloud computing services offered by Google
- Includes range of hosted services for computer, storage, app development

## 11. Terraform

- open-source tool for provisioning infrastructure resources
- supports DevOps best practices for change management
- able to manage config files in source control — infrastructure as code (IaC)
    - build, change, manage infrastructure in safe, consistent way

## Setup

- Install Terraform
    
    ```bash
    brew tap hashicorp/tap
    brew install hashicorp/tap/terraform
    ```
    
- Create GCP account with Google email
- Create a GCP project (e.g. name it `dtc-de`)
- Service account: allows services to interact w/ each other. For example, code running on VM can use this service account to give permissions
    - Create a service account `dtc-de-user`
    - Generate a GCP json key to interact with GCP resources
    - Install gcloud CLI
    - Authenticate to your GCP account with gcloud CLI
- Grant the service account `Storage Admin` , `Storage Object Admin` , and `BigQuery Admin` permissions so we can create a bucket
- Enable IAM and IAM Service Account Credentials APIs

## Terraform Project

- `.terraform-version`
    - specifies version of terraform to use

```
1.6.0
```

- `main.tf`
    
    ```
    terraform {
    	required_version = ">= 1.0"
    	backend "local" {} # where state is stored (can be "local", "gcs", "s3")
    	required_providers {
    		google = {
    			# provide registry/library that resources can be created from
    			source = "hashicorp/google"
    		}
    	}
    }
    
    providers "google" {
    	# var references a variables file variables.tf
    	project = var.project
    	region = var.region
    }
    
    # Create a google storage bucket
    resource "google_storage_bucket" "data-lake-bucket" {
      name          = "${local.data_lake_bucket}_${var.project}" # Concatenating bucket & project name for globally-unique name
      location      = var.region
    
      # Optional, but recommended settings:
      storage_class = var.storage_class
      uniform_bucket_level_access = true
    
      versioning {
        enabled     = true
      }
    
      lifecycle_rule {
        action {
          type = "Delete"
        }
        condition {
          age = 30  // days
        }
      }
    
      force_destroy = true
    }
    
    # DWH
    # Ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/bigquery_dataset
    resource "google_bigquery_dataset" "dataset" {
      dataset_id = var.BQ_DATASET
      project    = var.project
      location   = var.region
    }
    ```
    
- `variables.tf`
    
    ```
    
    locals {
    	data_lake_bucket = "dtc_data_lake"
    }
    
    variable "project" {
    	description "Your GCP Project ID"
    }
    
    variable "region" {
    	description = "Region for GCP resources. Choose as per your location"
    	default = "europe-west6"
    	type = string
    }
    
    # not used
    variable "bucket_name" {
    	description = "The name of the Google Cloud Storage bucket. Must be globally unique."
    	default = ""
    }
    
    variable "storage_class" {
    	description = "Storage class type for your bucket. Check official docs for more info."
    	default = "STANDARD"
    }
    
    variable "BQ_DATASET" {
    	description = "BigQuery Dataset that raw data (from GCS) will be written to"
    	type = string
    	default = "trips_data_all"
    }
    
    variable "TABLE_NAME" {
    	description = "BigQuery Table"
    	type = string
    	default = "ny_trips"
    }
    ```
    
- Commands to modify, create, update, destroy infrastructure stacks with Terraform
    
    ```bash
    # install required plugins (e.g. gcp provider)
    terraform init
    
    # compare changes to previous state
    terraform plan
    
    # apply changes to the cloud
    terraform apply
    
    # remove stack from the cloud
    terraform destroy
    ```