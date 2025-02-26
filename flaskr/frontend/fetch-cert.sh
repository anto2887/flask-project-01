#!/bin/sh

# Create directory for certificates
mkdir -p /etc/nginx/certs

# Export certificate from ACM
if [ -n "$ACM_CERTIFICATE_ARN" ]; then
  echo "Fetching certificate from ACM: $ACM_CERTIFICATE_ARN"
  
  # Get certificate details
  aws acm get-certificate --certificate-arn $ACM_CERTIFICATE_ARN > /tmp/cert.json
  
  # Extract certificate and chain
  cat /tmp/cert.json | jq -r '.Certificate' > /etc/nginx/certs/server.crt
  cat /tmp/cert.json | jq -r '.CertificateChain' >> /etc/nginx/certs/server.crt
  
  # Extract private key (Note: In a real scenario, you'd use AWS Secrets Manager for this)
  # This is a placeholder - you'll need to securely retrieve your private key
  echo "Private key needs to be securely retrieved and placed at /etc/nginx/certs/server.key"
  
  # Clean up
  rm /tmp/cert.json
else
  echo "ACM_CERTIFICATE_ARN not set, using self-signed certificate"
  # Generate self-signed certificate for development
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/certs/server.key \
    -out /etc/nginx/certs/server.crt \
    -subj "/CN=localhost"
fi

# Set proper permissions
chmod 600 /etc/nginx/certs/server.key
chmod 644 /etc/nginx/certs/server.crt

echo "Certificate setup complete" 