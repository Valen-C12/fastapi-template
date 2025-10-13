"""
S3 Client Integration

Provides a wrapper around boto3 for S3 operations with proper error handling.
Follows the Singleton pattern and includes common S3 operations.
"""

import logging
from typing import BinaryIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# S3 Client Class
# ============================================================================


class S3Client:
    """
    S3 client wrapper with common operations.

    This class implements the Singleton pattern and provides
    a simplified interface for S3 operations.
    """

    _instance: "S3Client | None" = None
    _client = None
    _resource = None

    def __new__(cls) -> "S3Client":
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> None:
        """
        Initialize S3 client.

        This method should be called during application startup.
        """
        if self._client is not None:
            logger.warning("S3 client already exists")
            return

        try:
            session = boto3.Session(
                aws_access_key_id=settings.s3_access_key_id,
                aws_secret_access_key=settings.s3_secret_access_key,
                region_name=settings.s3_region,
            )

            # Create client
            self._client = session.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url if settings.s3_endpoint_url else None,
            )

            # Create resource for higher-level operations
            self._resource = session.resource(
                "s3",
                endpoint_url=settings.s3_endpoint_url if settings.s3_endpoint_url else None,
            )

            # Test connection by listing buckets
            self._client.list_buckets()
            logger.info("S3 client initialized successfully")
        except (BotoCoreError, ClientError) as e:
            logger.error("Failed to initialize S3 client: %s", e)
            raise

    def disconnect(self) -> None:
        """Close S3 client connections."""
        if self._client:
            self._client.close()
            self._client = None
        if self._resource:
            self._resource = None
        logger.info("S3 client closed")

    def get_client(self):
        """
        Get S3 client instance.

        Returns:
            boto3 S3 client

        Raises:
            RuntimeError: If client is not initialized
        """
        if self._client is None:
            raise RuntimeError("S3 client not initialized. Call connect() first.")
        return self._client

    def get_resource(self):
        """
        Get S3 resource instance.

        Returns:
            boto3 S3 resource

        Raises:
            RuntimeError: If resource is not initialized
        """
        if self._resource is None:
            raise RuntimeError("S3 resource not initialized. Call connect() first.")
        return self._resource

    # ========================================================================
    # File Operations
    # ========================================================================

    def upload_file(
        self,
        file_path: str,
        object_key: str,
        bucket: str | None = None,
        extra_args: dict | None = None,
    ) -> bool:
        """
        Upload a file to S3.

        Args:
            file_path: Path to local file
            object_key: S3 object key (path in bucket)
            bucket: S3 bucket name (defaults to configured bucket)
            extra_args: Extra arguments for upload (e.g., {'ContentType': 'image/jpeg'})

        Returns:
            True if successful

        Raises:
            ClientError: If upload fails
        """
        bucket = bucket or settings.s3_bucket_name
        try:
            client = self.get_client()
            client.upload_file(file_path, bucket, object_key, ExtraArgs=extra_args)
            logger.info("Uploaded file %s to s3://%s/%s", file_path, bucket, object_key)
            return True
        except (BotoCoreError, ClientError) as e:
            logger.error("Failed to upload file %s: %s", file_path, e)
            raise

    def upload_fileobj(
        self,
        file_obj: BinaryIO,
        object_key: str,
        bucket: str | None = None,
        extra_args: dict | None = None,
    ) -> bool:
        """
        Upload a file object to S3.

        Args:
            file_obj: File-like object to upload
            object_key: S3 object key (path in bucket)
            bucket: S3 bucket name (defaults to configured bucket)
            extra_args: Extra arguments for upload

        Returns:
            True if successful

        Raises:
            ClientError: If upload fails
        """
        bucket = bucket or settings.s3_bucket_name
        try:
            client = self.get_client()
            client.upload_fileobj(file_obj, bucket, object_key, ExtraArgs=extra_args)
            logger.info("Uploaded file object to s3://%s/%s", bucket, object_key)
            return True
        except (BotoCoreError, ClientError) as e:
            logger.error("Failed to upload file object to %s: %s", object_key, e)
            raise

    def download_file(
        self,
        object_key: str,
        file_path: str,
        bucket: str | None = None,
    ) -> bool:
        """
        Download a file from S3.

        Args:
            object_key: S3 object key (path in bucket)
            file_path: Path to save downloaded file
            bucket: S3 bucket name (defaults to configured bucket)

        Returns:
            True if successful

        Raises:
            ClientError: If download fails
        """
        bucket = bucket or settings.s3_bucket_name
        try:
            client = self.get_client()
            client.download_file(bucket, object_key, file_path)
            logger.info("Downloaded s3://%s/%s to %s", bucket, object_key, file_path)
            return True
        except (BotoCoreError, ClientError) as e:
            logger.error("Failed to download %s: %s", object_key, e)
            raise

    def download_fileobj(
        self,
        object_key: str,
        file_obj: BinaryIO,
        bucket: str | None = None,
    ) -> bool:
        """
        Download a file from S3 to a file object.

        Args:
            object_key: S3 object key (path in bucket)
            file_obj: File-like object to write to
            bucket: S3 bucket name (defaults to configured bucket)

        Returns:
            True if successful

        Raises:
            ClientError: If download fails
        """
        bucket = bucket or settings.s3_bucket_name
        try:
            client = self.get_client()
            client.download_fileobj(bucket, object_key, file_obj)
            logger.info("Downloaded s3://%s/%s to file object", bucket, object_key)
            return True
        except (BotoCoreError, ClientError) as e:
            logger.error("Failed to download %s to file object: %s", object_key, e)
            raise

    def delete_file(self, object_key: str, bucket: str | None = None) -> bool:
        """
        Delete a file from S3.

        Args:
            object_key: S3 object key (path in bucket)
            bucket: S3 bucket name (defaults to configured bucket)

        Returns:
            True if successful

        Raises:
            ClientError: If deletion fails
        """
        bucket = bucket or settings.s3_bucket_name
        try:
            client = self.get_client()
            client.delete_object(Bucket=bucket, Key=object_key)
            logger.info("Deleted s3://%s/%s", bucket, object_key)
            return True
        except (BotoCoreError, ClientError) as e:
            logger.error("Failed to delete %s: %s", object_key, e)
            raise

    def file_exists(self, object_key: str, bucket: str | None = None) -> bool:
        """
        Check if a file exists in S3.

        Args:
            object_key: S3 object key (path in bucket)
            bucket: S3 bucket name (defaults to configured bucket)

        Returns:
            True if file exists
        """
        bucket = bucket or settings.s3_bucket_name
        try:
            client = self.get_client()
            client.head_object(Bucket=bucket, Key=object_key)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                return False
            logger.error("Error checking if %s exists: %s", object_key, e)
            raise

    def get_file_metadata(self, object_key: str, bucket: str | None = None) -> dict:
        """
        Get file metadata from S3.

        Args:
            object_key: S3 object key (path in bucket)
            bucket: S3 bucket name (defaults to configured bucket)

        Returns:
            Metadata dictionary

        Raises:
            ClientError: If operation fails
        """
        bucket = bucket or settings.s3_bucket_name
        try:
            client = self.get_client()
            response = client.head_object(Bucket=bucket, Key=object_key)
            return {
                "size": response.get("ContentLength"),
                "content_type": response.get("ContentType"),
                "last_modified": response.get("LastModified"),
                "etag": response.get("ETag"),
                "metadata": response.get("Metadata", {}),
            }
        except (BotoCoreError, ClientError) as e:
            logger.error("Failed to get metadata for %s: %s", object_key, e)
            raise

    def list_files(self, prefix: str = "", bucket: str | None = None, max_keys: int = 1000) -> list[dict]:
        """
        List files in S3 bucket with optional prefix.

        Args:
            prefix: Filter results by prefix
            bucket: S3 bucket name (defaults to configured bucket)
            max_keys: Maximum number of keys to return

        Returns:
            List of file metadata dictionaries

        Raises:
            ClientError: If operation fails
        """
        bucket = bucket or settings.s3_bucket_name
        try:
            client = self.get_client()
            response = client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=max_keys)

            files = []
            for obj in response.get("Contents", []):
                # Check all required keys exist before accessing
                if all(k in obj for k in ["Key", "Size", "LastModified", "ETag"]):
                    files.append(
                        {
                            "key": obj.get("Key", ""),
                            "size": obj.get("Size", 0),
                            "last_modified": obj.get("LastModified"),
                            "etag": obj.get("ETag", ""),
                        }
                    )

            return files
        except (BotoCoreError, ClientError) as e:
            logger.error("Failed to list files with prefix %s: %s", prefix, e)
            raise

    def generate_presigned_url(
        self,
        object_key: str,
        bucket: str | None = None,
        expiration: int = 3600,
        http_method: str = "get_object",
    ) -> str:
        """
        Generate a presigned URL for S3 object.

        Args:
            object_key: S3 object key (path in bucket)
            bucket: S3 bucket name (defaults to configured bucket)
            expiration: URL expiration time in seconds (default: 1 hour)
            http_method: HTTP method (get_object or put_object)

        Returns:
            Presigned URL string

        Raises:
            ClientError: If operation fails
        """
        bucket = bucket or settings.s3_bucket_name
        try:
            client = self.get_client()
            url = client.generate_presigned_url(
                http_method,
                Params={"Bucket": bucket, "Key": object_key},
                ExpiresIn=expiration,
            )
            logger.info("Generated presigned URL for s3://%s/%s", bucket, object_key)
            return url
        except (BotoCoreError, ClientError) as e:
            logger.error("Failed to generate presigned URL for %s: %s", object_key, e)
            raise


# ============================================================================
# Global Instance
# ============================================================================

s3_client = S3Client()


# ============================================================================
# Dependency for FastAPI
# ============================================================================


def get_s3():
    """
    FastAPI dependency to get S3 client.

    Usage:
        @router.post("/upload")
        async def upload_file(
            file: UploadFile,
            s3: S3Client = Depends(get_s3)
        ):
            s3.upload_fileobj(file.file, f"uploads/{file.filename}")
            return {"status": "uploaded"}
    """
    return s3_client
