GET_SECRET_CMD="docker run --rm -it -v ${HOME}/.aws:/root/.aws amazon/aws-cli"

#Pass on AWS profile env variable
if [ ! -z ${AWS_PROFILE} ]; then
	GET_SECRET_CMD="${GET_SECRET_CMD} --profile ${AWS_PROFILE}"
fi

${GET_SECRET_CMD} secretsmanager get-secret-value --region us-east-1 --secret-id AnsibleDevelopers --query SecretString --output text \
  | grep -o '"[^"]\+"' | sed 's/"//g'

if [ $? -ne 0 ]; then
	>&2 echo -e "Error while retrieving secret: ${secret1}\n"
	exit 1
fi
