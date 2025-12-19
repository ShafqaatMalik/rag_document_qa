# Deployment Guide

Complete deployment guide for Docker and AWS.

## Docker Deployment

### Local Development

```bash
docker-compose -f deployment/docker/docker-compose.yml up -d
```

### Production - Docker Hub

Build and push to Docker Hub:

```bash
docker build -f deployment/docker/Dockerfile -t your-username/rag-qa:latest .
docker push your-username/rag-qa:latest
```

Pull and run on any server:

```bash
docker pull your-username/rag-qa:latest
docker run -p 8000:8000 --env-file .env your-username/rag-qa:latest
```

## AWS EC2 Deployment

1. Launch Ubuntu 22.04 EC2 instance
2. Run deployment script:

```bash
chmod +x deployment/aws/ec2-setup.sh
./deployment/aws/ec2-setup.sh
```

3. Configure environment variables
4. Start services

## Environment Variables

Required environment variables:

- `GEMINI_API_KEY`: Your Gemini API key
- `DEBUG`: Debug mode (True/False)
- `LOG_LEVEL`: Logging level (INFO/DEBUG/WARNING)
- `CHROMA_PERSIST_DIRECTORY`: ChromaDB storage path

## Monitoring

### Health Checks

```bash
curl http://localhost:8000/api/v1/health
```

### Logs

```bash
# Docker logs
docker-compose logs -f

# Application logs
tail -f logs/app.log
```

## Security Considerations

- Never commit `.env` files
- Configure CORS appropriately
- Set up SSL/TLS certificates
- Implement rate limiting
- Use secrets management
