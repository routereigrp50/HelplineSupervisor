import azure.cognitiveservices.speech as speechsdk
from handlers.logging import Logging as h_log
import time


class Azure:
    def __init__(self, azure_api_key: str, azure_region: str, azure_language: str, audio_path: str, timeout: int = 60):
        self.api_key = azure_api_key
        self.region = azure_region
        self.language = azure_language
        self.audio_path = audio_path
        self.timeout = timeout

        self.recognition_result = []
        self.done = False
        self.failed = False
        self.fail_reason = None
        self.speaker_toggle = 0

        self.recognizer = self._init_recognizer()
        self._connect_event_handlers()

    def _init_recognizer(self) -> speechsdk.transcription.ConversationTranscriber:
        '''
        FUNCTION: CREATE RECOGNIZER OBJECT
        '''
        speech_config = speechsdk.SpeechConfig(subscription=self.api_key, region=self.region)
        speech_config.speech_recognition_language = self.language
        audio_config = speechsdk.audio.AudioConfig(filename=self.audio_path)
        return speechsdk.transcription.ConversationTranscriber(speech_config=speech_config, audio_config=audio_config)
    
    def transcribe(self) -> tuple:
        '''
        FUNCTION: CORE OF CLASS LOGIC. START TRANSCRIPTION WITH TIMEOUT HANDLING AND STATIC SPEAKER ASSIGNMENT
        '''
        h_log.create_log(4, "azure.transcribe", f"Attempting to transcribe file: {self.audio_path}")
        try:
            self.recognizer.start_transcribing_async()

            #TIMEOUT HANDLING: WAIT FOR THE TRANSCRIPTION TO COMPLETE OR FOR TIMEOUT
            start_time = time.time()
            while not self.done and (time.time() - start_time) < self.timeout:
                time.sleep(0.5)
            
            #CHECK IF TRANSCRIPTION WAS SUCCESSFUL OR IF IT TIMED OUT
            if not self.done:
                self.recognizer.stop_transcribing_async()
                self.failed = True
                self.fail_reason = "Transcription timed out"
                h_log.create_log(3, "azure.transcribe", f"Failed to transcribe file {self.audio_path}. Reason: Transcription timed out")
        
        except Exception as e:
            self.failed = True
            self.fail_reason = str(e)
            h_log.create_log(3, "azure.transcribe", f"Failed to transcribe file {self.audio_path}. Reason: {str(e)}")

        if self.failed:
            return (False, self.fail_reason)
        else:
            h_log.create_log(4, "azure.transcribe",f"Successfully transcribed file {self.audio_path}")
            return (True, "\n".join(self.recognition_result))
    
    def _connect_event_handlers(self) -> None:
        '''
        FUNCTION: CONNECT EVENT HANDLERS FOR TRANSCRIPTION EVENTS
        '''
        self.recognizer.session_started.connect(self._azure_callback_start)
        self.recognizer.transcribed.connect(self._azure_callback_handle_final_result)
        self.recognizer.canceled.connect(self._azure_callback_stop)
        

    def _azure_callback_start(self, evt) -> None:
        '''
        FUNCTION: CALLBACK FOR STARTING THE TRANSCRIPTION
        '''
        h_log.create_log(5, "azure._azure_callback_start", f"Transcription of file: {self.audio_path} started")

    def _azure_callback_stop(self, evt) -> None:
        '''
        FUNCTION: CALLBACK FOR STOPPING THE TRANSCRIPTION
        '''
        h_log.create_log(5, "azure._azure_callback_stop", f"Transcription of file: {self.audio_path} ended with status Success")
        self.done = True
    
    def _azure_callback_handle_final_result(self, evt) -> None:
        '''
        FUNCTION: HANDLE THE FINAL RESULT FROM EACH TRANSCRIPTION EVENT, ASSIGNING ALTERNATELY TO TWO SPEAKERS
        '''
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            speaker = "S1" if self.speaker_toggle == 0 else "S2"
            self.recognition_result.append(f"{speaker}: {evt.result.text}")

            self.speaker_toggle = 1 - self.speaker_toggle
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            self.recognition_result.append("Unrecognized speech segment")
        elif evt.result.reason == speechsdk.ResultReason.Canceled:
            self.failed = True
            self.fail_reason = "Transcription canceled by the service"
            self.done = True