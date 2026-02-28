# AWS Well-Architected Framework Pillar Skills

This file defines the Well-Architected Framework principles and recommended services for each pillar.
The system uses these recommendations to enrich architecture descriptions with production-grade best practices.

---

## Operational Excellence

**Focus:** Run and monitor systems to deliver business value and improve processes

**Core Principles:**
- Infrastructure as code (IaC) for repeatability
- Automation of operational tasks
- Structured logging and monitoring
- Regular review and improvement

**Recommended Services:**
- **AWS CloudFormation / AWS CDK**: Infrastructure as code for defining and managing resources
- **Amazon CloudWatch**: Metrics, logs, alarms, and dashboards for full observability
- **AWS X-Ray**: Distributed tracing for request flows and performance analysis
- **AWS CloudWatch Logs**: Centralized logging from all services
- **Amazon EventBridge**: Automates operational responses to system events
- **AWS Systems Manager**: Parameter Store for configuration, Session Manager for access
- **AWS OpsWorks / AWS Proton**: Automated deployment and management
- **AWS Config**: Continuous compliance monitoring and remediation

**Anti-patterns to avoid:**
- Manual operations (no automation)
- Logs scattered across services without centralization
- No alerting thresholds or runbooks
- Treating monitoring as an afterthought

---

## Security

**Focus:** Protect information, systems, and assets from unauthorized access

**Core Principles:**
- Defense in depth (multiple layers)
- Principle of least privilege (minimal permissions)
- Encryption in transit and at rest
- Regular security assessments and patching

**Recommended Services:**
- **AWS Identity and Access Management (IAM)**: Fine-grained access control
- **Amazon Cognito / AWS IAM Identity Center**: User authentication and federation
- **AWS Secrets Manager**: Rotate and manage secrets (API keys, DB passwords)
- **AWS Key Management Service (KMS)**: Encryption key management
- **AWS WAF**: Web application firewall for API/ALB protection
- **Amazon GuardDuty**: Threat detection using ML
- **AWS Shield Standard/Advanced**: DDoS protection
- **Amazon Macie**: Data discovery and protection for sensitive data
- **AWS Security Hub**: Centralized security monitoring
- **AWS Certificate Manager (ACM)**: SSL/TLS certificate management
- **Amazon Inspector**: Vulnerability assessments for EC2/containers
- **AWS VPC**: Network isolation, security groups, NACLs

**Anti-patterns to avoid:**
- Hard-coded credentials in code
- Overly permissive IAM policies (no least privilege)
- Unencrypted data at rest or in transit
- No multi-factor authentication (MFA)

---

## Reliability

**Focus:** Ensure systems are resilient and can recover from failures

**Core Principles:**
- Multi-AZ / Multi-region redundancy
- Automated recovery and failover
- Capacity planning and auto-scaling
- Regular disaster recovery testing

**Recommended Services:**
- **AWS Auto Scaling / Application Auto Scaling**: Automatic capacity adjustment
- **AWS Elastic Load Balancing (ALB/NLB)**: Distribute traffic across instances
- **Amazon Route 53**: DNS failover and health checks
- **AWS RDS (Multi-AZ)**: Database replication for high availability
- **Amazon DynamoDB**: Global tables for multi-region replication
- **Amazon ElastiCache**: Cache layer for resilience and performance
- **AWS Backup**: Automated backup and recovery
- **Amazon S3 Cross-Region Replication**: Geographic redundancy for data
- **AWS Lambda**: Inherently distributed, no server management
- **Amazon SQS**: Decouple services, retry logic, dead-letter queues
- **Amazon SNS**: Fan-out messaging for reliability
- **AWS CloudFormation StackSets**: Multi-region, multi-account deployments

**Anti-patterns to avoid:**
- Single points of failure (single AZ, single database)
- No backup strategy
- Manual failover processes
- Tight coupling between services

---

## Performance Efficiency

**Focus:** Use resources efficiently to meet system requirements and maintain that efficiency as demand changes

**Core Principles:**
- Right-sizing resources for workload
- Using managed services to offload operational burden
- Caching and content delivery
- Database optimization and indexing

**Recommended Services:**
- **Amazon CloudFront**: CDN for global content distribution
- **Amazon ElastiCache**: In-memory caching (Redis/Memcached)
- **Amazon RDS Read Replicas**: Database read scaling
- **Amazon DynamoDB**: On-demand/provisioned capacity scaling
- **AWS Lambda**: Pay-per-use compute, auto-scales instantly
- **Amazon OpenSearch Service**: Full-text and vector search with indexing
- **Amazon Redshift**: Data warehouse optimized for analytics
- **Amazon Athena**: Serverless SQL queries on S3
- **AWS Global Accelerator**: Improved global performance
- **Amazon SageMaker**: ML model optimization and inference
- **AWS Graviton Processors**: Cost-effective compute instances
- **Amazon EBS Provisioned IOPS**: High-performance block storage

**Anti-patterns to avoid:**
- Over-provisioned resources (wasting money)
- Under-provisioned resources (poor user experience)
- Monolithic databases (no read replicas, sharding)
- No caching layer (repeated expensive queries)

---

## Cost Optimization

**Focus:** Avoid unnecessary costs and maximize value from AWS spending

**Core Principles:**
- Right-sizing instances and resources
- Using spot instances for flexible workloads
- Reserved capacity for committed workloads
- Monitoring and alerting on cost anomalies

**Recommended Services:**
- **AWS Compute Optimizer**: Right-sizing recommendations
- **AWS Cost Explorer**: Cost analysis and trend visualization
- **AWS Budgets**: Set spending limits and alerts
- **AWS Trusted Advisor**: Best practices and cost optimization checks
- **EC2 Spot Instances**: Up to 90% discount for fault-tolerant workloads
- **AWS Savings Plans / Reserved Instances**: Commitment discounts
- **AWS Lambda**: Pay-per-invocation (no server rental)
- **Amazon DynamoDB On-Demand**: Pay-per-request (no over-provisioning)
- **Amazon S3 Lifecycle Policies**: Archive old data to Glacier
- **AWS Data Transfer**: Minimize inter-region data movement
- **Amazon CloudWatch Logs Insights**: Query logs efficiently without exporting
- **AWS Glue Data Catalog**: Metadata management without redundant storage

**Anti-patterns to avoid:**
- Leaving unused resources running (untagged resources, old snapshots)
- Over-provisioned database capacity
- No lifecycle policies for S3 (old data stays expensive)
- Not reviewing Reserved Instance utilization

---

## Integration Pattern: Well-Architected Checks

When generating architectures, apply these checks per pillar:

| Pillar | Check | Recommended If Missing |
|--------|-------|------------------------|
| **Operational Excellence** | Has CloudWatch + X-Ray + centralized logging? | Add CloudWatch, CloudWatch Logs, X-Ray |
| **Security** | Has WAF + authentication + encryption + secrets mgmt? | Add WAF, Cognito, KMS, Secrets Manager, GuardDuty |
| **Reliability** | Has multi-AZ + auto-scaling + backups + failover? | Add ALB/NLB, Auto Scaling, RDS Multi-AZ, Route53, AWS Backup |
| **Performance** | Has caching + CDN + database read replicas? | Add CloudFront, ElastiCache, RDS read replicas |
| **Cost** | Has right-sizing strategy + reserved capacity + monitoring? | Add AWS Budgets, Cost Explorer, Compute Optimizer, S3 Lifecycle |

---

## Example: E-commerce Platform with All 5 Pillars

**Operational Excellence:**
- CloudFormation for infrastructure
- CloudWatch + CloudWatch Logs + X-Ray for observability
- EventBridge for automated responses

**Security:**
- VPC with public/private subnets
- WAF on ALB and CloudFront
- Cognito for user authentication
- KMS for encryption (RDS, S3, DynamoDB)
- Secrets Manager for API keys and DB passwords
- GuardDuty for threat detection
- IAM roles with least privilege

**Reliability:**
- Multi-AZ RDS with automated backups
- ElastiCache for session resilience
- SQS for decoupling and retries
- Auto Scaling Groups for compute redundancy
- Route 53 health checks for failover

**Performance:**
- CloudFront CDN for static assets
- ElastiCache Redis for hot data
- RDS read replicas for read-heavy queries
- OpenSearch for product search indexing
- DynamoDB for low-latency sessions

**Cost Optimization:**
- Lambda for burst processing (pay-per-use)
- DynamoDB on-demand for variable traffic
- S3 Lifecycle policies for log archival
- Reserved Instances for predictable baseline

---
