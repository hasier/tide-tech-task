# Tide programming task
Simple AWS Lambda + API Gateway project of an API call to enable feature switches in client apps.

## Purpose
In order to dynamically enable and disable features in mobile apps, the following structure is proposed:
* Each time the app is freshly launched, the client app will make a request to the given endpoint.
* The call should be authenticated as it is with any other API call. If it is not, only globally enabled features will be considered.
* The endpoint will return a list of enabled features for that particular user (if authenticated) plus the globally available ones.
* The client app should enable or disable features as the provided list indicates.

Following this procedure, if a major bug appears or the behaviour is not the desired one, simply modifying the setting from the backoffice will disable that feature for all clients.

## General structure
The proposed solution has been thought bearing the following ideas in mind:
* It needs to have some kind of authentication, in order to check that users requesting info are who they claim. The solution contains basic authentication, but it should not be difficult to adapt it to other solutions.
* The endpoint will have to bear with a huge load, so the execution needs to be quick and with little overhead. The solution is based on Python and Redis, which should be quick enough to check and return values.
* Another similar procedure can be created in the same function so that backoffice users can modify the feature switches.

## Setup
`lambda-microservice.py` contains an AWS Lambda function that is routed from an API Gateway. The setup (very briefly) would be as follows:
* Create a Python Lambda function
* Add the code from `lambda-microservice.py` and name it, say "FeatureSwitchLambda"
* If needed, add an IAM role, otherwise just continue
* Create an API Gateway with the desired route, say called "FeatureSwitchService" and routed as a GET request to `/api/v1/features`
* Associate "FeatureSwitchLambda" with the gateway
* In Mapping Templates, add a map for the headers in the request
```
{
  "headers": {
    #foreach($param in $input.params().header.keySet())
    "$param": "$util.escapeJavaScript($input.params().header.get($param))" #if($foreach.hasNext),#end
    
    #end  
  }
}
```
And a map for the errors in the response
```
#set ($errorMessageObj = $util.parseJson($input.path('$.errorMessage')))
{
  "type" : "$errorMessageObj.errorType",
  "message" : "$errorMessageObj.message",
  "request-id" : "$errorMessageObj.requestId"
}
```

This system also relies on the following:
* There is a Redis instance for user authentication, where keys are formated as:
<pre>
<b>key => value</b>
token1 => user_id_1
token2 => user_id_2
...
</pre>
* There is a Redis instance for the feature switches, where keys are formated as:
<pre>
<b>key => value</b>
global_features => set_of_features (feature string names added with sadd)
active_features => set_of_features (feature string names added with sadd)
features:user:user_id_1 => set_of_features (feature string names added with sadd)
features:user:user_id_2 => set_of_features (feature string names added with sadd)
...
</pre>
   The `global_features` contain all the ones that are openly available.  
   The `active_features` contain all the ones that each user might have personally active.  
   The entries for each user contain all the ones that the user is entitled to, as long as they are active in `active_features`.  

## Future work
This is a quick approach to feature switches, but the work could be extended to be used in different locations, schedules, etc.
For instance, a new set of keys could be added to the Redis with feature switches, such as:
```
location:location1 => set_of_features
location:location2 => set_of_features
```
This way we could get the name of the location of the user (or checking with the IP, or any other method) and apply an extra set of different features.
