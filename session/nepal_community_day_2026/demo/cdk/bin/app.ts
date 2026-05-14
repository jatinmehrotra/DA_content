#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { IacDemoStack } from '../lib/iac-demo-stack';

const app = new cdk.App();

new IacDemoStack(app, 'IacDemoCdkStack', {
  description: 'IaC Demo - S3 Bucket and Lambda Function (CDK)',
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
});
