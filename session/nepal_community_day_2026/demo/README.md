eiifcbnbjtjgfcedhbelelceikghbcggrcikjvevkrfn
# IaC Demo — Same Task, Three Tools

Each folder creates the same infrastructure:
- **S3 Bucket** (encrypted, versioned, public access blocked)
- **Lambda Function** (Python 3.12, returns a hello message)

## CloudFormation

```bash
aws cloudformation deploy \
  --template-file demo/cloudformation/template.yaml \
  --stack-name iac-demo-cfn \
  --capabilities CAPABILITY_IAM
```

**Cleanup:**
```bash
aws cloudformation delete-stack --stack-name iac-demo-cfn
```

## CDK

```bash
cd demo/cdk
npm install
npx cdk deploy
```

**Cleanup:**
```bash
npx cdk destroy
```

## Terraform

```bash
cd demo/terraform
terraform init
terraform plan
terraform apply
```

**Cleanup:**
```bash
terraform destroy
```

## Best Practices Applied

All three implementations follow the same security best practices:

| Practice | CloudFormation | CDK | Terraform |
|----------|---------------|-----|-----------|
| S3 encryption (AES-256) | ✅ | ✅ | ✅ |
| S3 public access blocked | ✅ | ✅ | ✅ |
| S3 versioning enabled | ✅ | ✅ | ✅ |
| S3 enforce SSL | — | ✅ | — |
| Lambda least-privilege IAM | ✅ | ✅ (auto) | ✅ |
| Lambda explicit timeout | ✅ | ✅ | ✅ |
| Lambda explicit memory | ✅ | ✅ | ✅ |
| IAM assume role policy (data source) | — | — | ✅ |
| Separate resource configs (not deprecated) | — | — | ✅ |

### Notes
- **CDK** automatically creates the Lambda execution role with least-privilege — no manual IAM definition needed
- **CDK** uses `grant()` methods for cross-resource permissions (e.g., `bucket.grantRead(fn)`)
- **Terraform** uses separate resources for bucket versioning, encryption, and public access block (following current best practices, avoiding deprecated inline arguments)
- **Terraform** uses `data "aws_iam_policy_document"` for type-safe IAM policy definition
- **CloudFormation** is the most explicit — every resource and property is declared manually

---

## Learning Resources

> 🆕 **2025–2026 links are listed first** in each section to help readers find the most current content.

### AWS CDK

**2025–2026 Tutorials & Guides**
- [Build Your First AWS CDK Stack](https://www.datacamp.com/tutorial/aws-cdk) — DataCamp, May 2025. Python-focused beginner tutorial.
- [AWS CDK Examples](https://github.com/aws-samples/aws-cdk-examples) — Official aws-samples repo, actively maintained. TypeScript, Python, Java, Go, .NET.
- [Generative AI CDK Constructs Samples](https://github.com/aws-samples/generative-ai-cdk-constructs-samples) — Modern AI/ML stacks built with CDK.

**Official Docs & Workshops**
- [Create your first CDK app](https://docs.aws.amazon.com/cdk/v2/guide/hello-world.html) — Official AWS tutorial (Lambda + Function URL).
- [Serverless Hello World with CDK](https://docs.aws.amazon.com/cdk/v2/guide/serverless-example.html) — API Gateway + Lambda tutorial.
- [CDK Workshop](https://cdkworkshop.com) — The classic hands-on workshop (TypeScript, Python, Java, .NET).
- [AWS CDK v2 Developer Guide](https://docs.aws.amazon.com/cdk/v2/guide/home.html) — Full reference documentation.

---

### Terraform

**2025–2026 Tutorials & Guides**
- [Terraform on AWS: Complete Beginner's Guide](https://www.terraformpilot.com/articles/terraform-on-aws-a-complete-beginners-guide/) — TerraformPilot, Feb 2026. Provider setup, S3, EC2, VPC, remote state.
- [Terraform on AWS: Complete Beginner Guide 2026](https://atmosly.com/knowledge/terraform-on-aws-the-most-complete-beginner-guide-for-2025) — Atmosly. Zero to working project with best practices.
- [Terraform AWS Tutorial: Automating EC2](https://www.datacamp.com/tutorial/terraform-aws) — DataCamp, Jan 2025. Real-world EC2 + SSM example.
- [Terraform Tutorial — Getting Started](https://spacelift.io/blog/terraform-tutorial) — Spacelift, 2026. Covers full workflow step-by-step.
- [12-Step Terraform AWS Tutorial](https://tech-insider.org/terraform-tutorial-aws-infrastructure-as-code-2026/) — Tech Insider, 2026. From install to multi-environment deployment.
- [Terraform Zero to Hero with AWS (Udemy)](https://www.udemy.com/course/terraform-zero-to-hero-with-aws-hands-on-for-beginners-2026/?couponCode=TERRAFORMFREE) — Free course, 2026. Workspaces, environments, state management.

**Official & Community**
- [Get Started with AWS — HashiCorp](https://developer.hashicorp.com/terraform/tutorials/aws-get-started) — Official step-by-step tutorials (init, plan, apply, destroy).
- [Terraform Zero to Hero](https://github.com/iam-veeramalla/terraform-zero-to-hero) — 7-day structured course with code samples.
- [Terraform: Up & Running Code](https://github.com/brikis98/terraform-up-and-running-code) — Code samples from the popular book (3rd edition).

---

### AWS CloudFormation

**2025–2026 Tutorials & Guides**
- [CloudFormation 2025 Year in Review](https://aws.amazon.com/blogs/devops/aws-cloudformation-2025-year-in-review/) — AWS Blog, Jan 2026. New features: early validation, drift management, IDE integration.
- [AWS CloudFormation Samples](https://github.com/aws-cloudformation/aws-cloudformation-samples) — Official sample templates, actively maintained.

**Official Workshops & Docs**
- [CFN 101 Workshop](https://cfn101.workshop.aws) — The official CloudFormation workshop by AWS ([GitHub repo](https://github.com/aws-samples/cfn101-workshop)).
- [AWS CloudFormation Workshops](https://github.com/aws-samples/aws-cloudformation-workshops) — Additional workshop exercises.
- [Getting Started with CloudFormation](https://aws.amazon.com/cloudformation/getting-started/) — Official getting started page with Language Server info.
- [AWS Workshops Catalog](https://catalog.workshops.aws) — Search "CloudFormation" for dozens of free hands-on workshops.

---

### General IaC Learning

- [AWS Workshops](https://catalog.workshops.aws) — Free self-guided tutorials across all AWS services.
- [AWS Global Summits](https://aws.amazon.com/events/summits/) — Free in-person events with hands-on IaC workshops.
