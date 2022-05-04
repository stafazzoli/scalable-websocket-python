# Scaling Websockets in Python

Scaling websockets across multiple servers is not as straightforward as with a typical REST API.
Generally, a webSocket client opens up a connection to the server and reuses it. The connection stays open with the same server until it is closed.  
When we cluster servers, the load-balancer manages the distribution between instances and each websocket connection is bound to a specific instance.  
The challenge lies with this stateful connection between a client and an instance. 

The easiest option is to introduce communication between different instances is a publish/subscribe broker. There are many ready-to-go solutions, like Redis, Kafka, or Nats.
In this implementation of scalable websockets, we use Redis pub/sub pattern. We also used [websockets](https://pypi.org/project/websockets/) module which handles opening and closing handshakes, pings and pongs between client and server.

1- When the client connects to an instance via a websocket connection, the server subscribe the user to a Redis channel (named the user's username).  

2- When the back-end wants to send a message to the user, it checks with a channel with user's username exists. If it does, it will publish the message to the channel.  

3- As the subscribed user checks the channel continuously, it will get the message and sends it to the user via the open websocket connection.  

4- Whenever the connection between the client and server closes, the user unsubscribe from the Redis channel and closes the Redis  pub/sub connection.  

As you can see, instead of sending messages to the webSocket client right away, we publish them on a channel and then handle them separately. By doing this, we’re sure that the message is published to every instance and then sent to users.

## Dependency Installations
To run the project, install the dependencies using the command below:
```bash
pip install -r requirements.txt
```
Also, create a `logs` folder in the project root where logs are saved.

## Testing Websocket connections
You can find a client sample code in `test` folder that you can use test how the opening and closing the connection is handled in the code.