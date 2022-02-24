<template>
  <input v-model="todo" placeholder="add todo" v-on:keyup.enter="add_todo(todo)">
  <button 
      v-on:click.passive="add_todo(todo)"
  >
  add todo
  </button>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Home-yo',
  data(){
      return {todo: ""}
    },
  methods: {
    add_todo: function(message){
      axios.post('http://127.0.0.1:5000/api/add', {
        text: message,
      }).then(function(ret) {
          console.log(ret)
      })
      this.todo = ""
    }

      
  },
}
</script>
