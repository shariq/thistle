      //var Datared = new Firebase('https://uwyfjh6p0t4.firebaseio-demo.com/');
       var Datared = new Firebase('https://thistle-io.firebaseio.com/');
      $('#messageInput').keypress(function (e) {
        if (e.keyCode == 13) {
          //var name = $('#nameInput').val();
          var text = $('#messageInput').val();
          if (text == "") {
            return;
          }
          // username and roomURL need to be filled up
          var roomURL = 'room_0';
          var userName = 'user1';
          var roomRef = Datared.child(roomURL);
          roomRef.child(userName).child('in').child((new Date()).getTime().toString()).set(text);
          //debugger;
//          roomRef.update(updateVal);


          //Datared.push({name: name, text: text});
          $('#messageInput').val('');
        }
      });
      Datared.on('child_added', function(snapshot) {
        var message = snapshot.val();
        displayChatMessage(message.name, message.text);
      });
      function displayChatMessage(name, text) {
        $('<div/>').text(text).prepend($('<em/>').text(name+': ')).appendTo($('#messagesDiv'));
        $('#messagesDiv')[0].scrollTop = $('#messagesDiv')[0].scrollHeight;
      };