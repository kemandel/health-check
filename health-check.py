import sys
import asyncio
from urllib.parse import urlparse
from enum import Enum

import yaml
import requests

REQUESTS_DELAY = 15 # How often the program checks the endpoints

# State of the site endpoint
class SiteState(Enum):
  UP = 1
  DOWN = 2

# Read in the YAML file data and return if valid
def read_file(path):
  with open(path) as stream:
    try:
      return yaml.safe_load(stream)
    except yaml.YAMLError as exc:
      print(exc)

# Makes a request at each endpoints and returns the resulting latency, status code, and domain name
def check_site_health(endpoints):
  health_results = []
  for endpoint in endpoints:
    url = endpoint['url']
    headers = endpoint['headers'] if 'headers' in endpoint else None
    body = endpoint['body'] if 'body' in endpoint else None
  
    # POST
    if ('method' in endpoint and endpoint['method'] == 'POST'):
      response = requests.post(url = url, headers = headers, json = body)
    # GET
    else:
      response = requests.get(url = url, headers = headers, json = body)

    # Record the status code, latency, and domain of the endpoint request
    health_results.append({'name':endpoint['name'],'status_code':response.status_code, 'latency':response.elapsed.total_seconds(), 'domain':urlparse(url).netloc})

  return health_results

# Logs the final result of endpoint tests based on latency and status code, grouping endpoints by domain
def log_results(health_results):
  domains = {}
  for result in health_results:
    # Set state of result 
    result['state'] = SiteState.UP if 200 <= result['status_code'] < 300 and result['latency'] < .5 else SiteState.DOWN 
    # Add result to domain
    if result['domain'] in domains:
      domains[result['domain']].append(result)
    else:
      domains[result['domain']] = [result]
  
  # Calculate percentage of available endpoints for each domain
  for domain in domains.keys():
    up_count = 0
    for result in domains[domain]:
      if result['state'] == SiteState.UP:
        up_count += 1
    percent = int(100 * up_count / len(domains[domain]))
    # Log results
    print(domain + " has " + str(percent) +"% availability percentage")

# Reads in a yaml file and tests the configured endpoints once every REQUESTS_DELAY seconds
async def main():
  # If the failed to input exactly 1 argument
  if len(sys.argv) != 2:
    raise Exception("Invalid command line argument! Input (1) path to yaml file.")
  
  endpoint_data = read_file(sys.argv[1]) # Read in yaml data from path

  while (True):
    log_results(check_site_health(endpoint_data))
    await asyncio.sleep(REQUESTS_DELAY)
    

if __name__ == "__main__":
  asyncio.run(main())