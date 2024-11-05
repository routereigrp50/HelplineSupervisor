
# HelplineSupervisor

Web and microservice based script that allows you to assess the performance of helpline employees in terms of the quality of customer service.




## Requirements

* Azure Cognitive Services subscription
* Azure OpenAI subscription
* MongoDB installed or MongoDB Cloud URI
* Directory with prepared .wav files


## Deployment

* Pull repository
* Edit config.json with desired api parameters and valid MongoDB uri
* Run docker compose file


```bash
  docker compose up --build
```

* Proceed to http://<service_ip><service_port>/docs to read the API documentation