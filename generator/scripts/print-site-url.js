const { execFileSync } = require('node:child_process')

const stageIndex = process.argv.indexOf('--stage')
const stage = stageIndex >= 0 ? process.argv[stageIndex + 1] : 'dev'
const region = process.env.AWS_REGION || process.env.AWS_DEFAULT_REGION || 'eu-central-1'
const stackName = `qrless-${stage}`

try {
  const siteUrl = execFileSync(
    'aws',
    [
      'cloudformation',
      'describe-stacks',
      '--stack-name',
      stackName,
      '--region',
      region,
      '--query',
      "Stacks[0].Outputs[?OutputKey=='SiteUrl'].OutputValue | [0]",
      '--output',
      'text',
    ],
    { encoding: 'utf8' }
  ).trim()

  if (siteUrl && siteUrl !== 'None') {
    console.log('')
    console.log(`Website URL: ${siteUrl}`)
  }
} catch (error) {
  console.log('')
  console.log(`Website URL: run "aws cloudformation describe-stacks --stack-name ${stackName} --region ${region} --query \\"Stacks[0].Outputs\\""`)
}
