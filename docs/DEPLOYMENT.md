# Deployment Guide

Complete deployment guide for various platforms.

## Docker Deployment

### Local Development

```bash
docker-compose -f deployment/docker/docker-compose.yml up -d
```

### Production

Build and push to container registry:

```bash
docker build -f deployment/docker/Dockerfile -t rag-qa:latest .
docker push your-registry/rag-qa:latest
```

## Render Deployment

1. Connect GitHub repository
2. Set environment variables
3. Deploy automatically on push

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
