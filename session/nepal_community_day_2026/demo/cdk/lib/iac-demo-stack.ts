import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export class IacDemoStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // S3 Bucket — L2 construct with security best practices
    // CDK applies sensible defaults: encryption, block public access
    const bucket = new s3.Bucket(this, 'DemoBucket', {
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: true,
      enforceSSL: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // Lambda Function — CDK automatically creates the IAM execution role
    const fn = new lambda.Function(this, 'DemoFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',
      code: lambda.Code.fromInline(`
import json

def handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Hello from CDK!",
            "tool": "AWS CDK"
        })
    }
      `),
      timeout: cdk.Duration.seconds(10),
      memorySize: 128,
    });

    // Grant Lambda read access to the bucket using CDK's grant methods
    bucket.grantRead(fn);

    // Outputs — CDK generates names, export them for reference
    new cdk.CfnOutput(this, 'BucketName', {
      value: bucket.bucketName,
      description: 'Name of the S3 bucket',
    });

    new cdk.CfnOutput(this, 'FunctionArn', {
      value: fn.functionArn,
      description: 'ARN of the Lambda function',
    });
  }
}
