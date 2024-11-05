
# HelplineSupervisor

Web and microservice based script that allows you to assess the performance of helpline employees in terms of the quality of customer service.




## Requirements

* Azure Cognitive Services subscription
* Azure OpenAI subscription
* MongoDB installed or MongoDB Cloud URI
* Directory with prepared .wav files


## How it works

* Each container works with an API that can be used to configure / stop / start a given job
* Proceed to http://<service_ip>:<service_port>/docs to read the API documentation
* Run first job - audio_prospector. Audio Prospector job is responsible for finding .wav files and adding them to the queue
* Run second job - speech_recognizer. Sppech Recognizer job is responsible for sending .wav files to azure cloud for speech to text conversion
* Run third job - conversation_peeper. Conversation Peeper job is responsible for assessing the quality of the conversation using artificial intelligence


Each job and container is independent of each other. This means they can operate at the same time.


## Deployment

* Pull repository
* Edit config.json with desired api parameters and valid MongoDB uri
* Run docker compose file


```bash
  docker compose up --build
```

* Proceed to http://<service_ip><service_port>/docs to read the API documentation
