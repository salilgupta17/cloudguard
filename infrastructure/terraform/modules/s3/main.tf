# CloudGuard Disaster Recovery Reports & Evidence Vault
# Encrypted S3 bucket with strict public access blocks and lifecycle governance

resource "aws_kms_key" "s3_key" {
  description             = "KMS Key for CloudGuard S3 Disaster Recovery Reports"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name        = "cloudguard-s3-kms-key"
    Environment = var.environment
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "reports" {
  bucket        = "${var.bucket_name_prefix}-${var.environment}-${random_id.bucket_suffix.hex}"
  force_destroy = false

  tags = {
    Name        = "cloudguard-dr-reports"
    Environment = var.environment
    Service     = "CloudGuard"
  }
}

resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.reports.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sse" {
  bucket = aws_s3_bucket.reports.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.s3_key.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

# Strict Block Public Access
resource "aws_s3_bucket_public_access_block" "block_public" {
  bucket = aws_s3_bucket.reports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle Configuration (Tiering & Cost Control)
resource "aws_s3_bucket_lifecycle_configuration" "lifecycle" {
  bucket = aws_s3_bucket.reports.id

  rule {
    id     = "dr-artifacts-lifecycle"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER_IR" # Glacier Instant Retrieval
    }

    expiration {
      days = 365
    }

    noncurrent_version_expiration {
      noncurrent_days = 60
    }
  }
}

# Enforce TLS / HTTPS only
resource "aws_s3_bucket_policy" "enforce_tls" {
  bucket = aws_s3_bucket.reports.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid       = "EnforceTLSRequestsOnly",
        Effect    = "Deny",
        Principal = "*",
        Action    = "s3:*",
        Resource = [
          aws_s3_bucket.reports.arn,
          "${aws_s3_bucket.reports.arn}/*"
        ],
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}
