#!/usr/bin/env python
"""
S3/MinIO Bucket Configuration Script

This script helps you configure bucket policies and settings.

Usage:
    python scripts/configure_s3_bucket.py
"""

import json

import boto3
from botocore.exceptions import ClientError

# Configuration (adjust these)
ENDPOINT_URL = "http://localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"  # noqa: S105  # This is a default/example value, not a real secret
BUCKET_NAME = "my-bucket"


def create_s3_client():
    """Create and return S3 client."""
    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )


def create_bucket(s3_client, bucket_name):
    """Create bucket if it doesn't exist."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' already exists")
    except ClientError:
        try:
            s3_client.create_bucket(Bucket=bucket_name)
            print(f"✅ Created bucket '{bucket_name}'")
        except Exception as e:
            print(f"❌ Failed to create bucket: {e}")
            raise


def set_public_read_policy(s3_client, bucket_name):
    """Set bucket policy to allow public read access."""
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket_name}/*"],
            }
        ],
    }

    try:
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
        print(f"✅ Set public read policy on '{bucket_name}'")
    except Exception as e:
        print(f"❌ Failed to set policy: {e}")
        raise


def set_private_policy(s3_client, bucket_name):
    """Remove bucket policy (make private)."""
    try:
        s3_client.delete_bucket_policy(Bucket=bucket_name)
        print(f"✅ Removed policy from '{bucket_name}' (now private)")
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "NoSuchBucketPolicy":
            print(f"ℹ️  Bucket '{bucket_name}' already has no policy (private)")
        else:
            print(f"❌ Failed to remove policy: {e}")
            raise


def set_custom_policy(s3_client, bucket_name, policy_dict):
    """Set custom bucket policy."""
    try:
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy_dict))
        print(f"✅ Set custom policy on '{bucket_name}'")
    except Exception as e:
        print(f"❌ Failed to set custom policy: {e}")
        raise


def get_bucket_policy(s3_client, bucket_name):
    """Get current bucket policy."""
    try:
        response = s3_client.get_bucket_policy(Bucket=bucket_name)
        policy = json.loads(response["Policy"])
        print(f"\n📋 Current policy for '{bucket_name}':")
        print(json.dumps(policy, indent=2))
        return policy
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "NoSuchBucketPolicy":
            print(f"ℹ️  Bucket '{bucket_name}' has no policy (private)")
            return None
        else:
            print(f"❌ Failed to get policy: {e}")
            raise


def enable_cors(s3_client, bucket_name):
    """Enable CORS for bucket."""
    cors_configuration = {
        "CORSRules": [
            {
                "AllowedHeaders": ["*"],
                "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
                "AllowedOrigins": ["*"],
                "ExposeHeaders": ["ETag"],
                "MaxAgeSeconds": 3000,
            }
        ]
    }

    try:
        s3_client.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=cors_configuration)
        print(f"✅ Enabled CORS on '{bucket_name}'")
    except Exception as e:
        print(f"❌ Failed to enable CORS: {e}")
        raise


def main():
    """Main function - interactive bucket configuration."""
    print("🪣 S3/MinIO Bucket Configuration Tool\n")

    s3_client = create_s3_client()

    # Create bucket if needed
    create_bucket(s3_client, BUCKET_NAME)

    # Show menu
    while True:
        print("\n" + "=" * 50)
        print("Options:")
        print("1. View current bucket policy")
        print("2. Set bucket to PUBLIC (read-only)")
        print("3. Set bucket to PRIVATE")
        print("4. Enable CORS")
        print("5. Set custom policy")
        print("6. Exit")
        print("=" * 50)

        choice = input("\nEnter your choice (1-6): ").strip()

        if choice == "1":
            get_bucket_policy(s3_client, BUCKET_NAME)

        elif choice == "2":
            confirm = input(f"⚠️  Make '{BUCKET_NAME}' publicly readable? (yes/no): ")
            if confirm.lower() == "yes":
                set_public_read_policy(s3_client, BUCKET_NAME)
                print("\n⚠️  WARNING: All objects in this bucket are now publicly accessible!")

        elif choice == "3":
            set_private_policy(s3_client, BUCKET_NAME)

        elif choice == "4":
            enable_cors(s3_client, BUCKET_NAME)

        elif choice == "5":
            print("\nExample custom policy (public read-write):")
            example_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
                        "Resource": [f"arn:aws:s3:::{BUCKET_NAME}/*"],
                    }
                ],
            }
            print(json.dumps(example_policy, indent=2))

            use_example = input("\nUse this example? (yes/no): ")
            if use_example.lower() == "yes":
                set_custom_policy(s3_client, BUCKET_NAME, example_policy)
            else:
                print("Policy not applied. Edit the script to add your custom policy.")

        elif choice == "6":
            print("\n👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)
