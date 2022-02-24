<template>
<div v-if="this.$store.state.list.length > 0">
  <div class="table-body" align="center">
    <thead>
      <tr>
        <th> Text </th> 
        <th> Date added </th> 
        <th> Status </th> 
        <th> Actions </th> 
        <th> Subtasks </th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="todo in todos" :key="todo.id">
        <td id="table-entry">
          <div v-show="editing != todo.id">{{todo.text}}</div>
          <input type="text" :id=todo.id v-model=edit v-show="editing == todo.id" placeholder="placeholder" v-on:keyup.enter="edit_todo(todo.id, this.edit)">
        </td>
        <td id="table-entry">{{todo.date}}</td>
        <td id="table-entry"><input type="checkbox" v-model=todo.done @click=mark_done(todo.id)></td>
        <td id="table-entry">
          <button @click=delete_todo(todo.id)>delete</button>
          <button @click="add_subtask(todo.id, this.subtask)" v-show="writingSubtask == todo.id">add subtask</button>
          <button @click="enable_editing_subtask(todo.id)" v-show="writingSubtask != todo.id">write subtask</button>
          <button @click="enable_editing(todo.id, todo.text)" v-show="editing != todo.id">edit</button>
          <button @click="edit_todo(todo.id, this.edit)" v-show="editing == todo.id">send</button>
        </td>
        <td id="table-entry">
          <div v-show="writingSubtask != todo.id" v-for="subtask in JSON.parse(todo.subtasks)" :key="subtask.id">
           {{ subtask.text }}
          </div>
          <input type="text" v-model=subtask v-show="writingSubtask == todo.id" placeholder="add subtask" v-on:keyup.enter="add_subtask(todo.id, subtask)">
        </td>
      </tr>
    </tbody>
  </div>
  </div>
  <div v-else>
    You are done for today :)
  </div>
  <br>
  <button @click=download_export()>
    download export
  </button>
  <button @click=download_logs()>
    download logs
  </button>



</template>

<script>
import axios from 'axios'

export default {
  name: 'Todo-List',
  data() {
      return {
          editing: 0,
          edit: "",
          writingSubtask: 0,
          subtask: "",
        }
    },
  methods: {
      mark_done: function(id){
        axios.post('http://127.0.0.1:5000/api/done', {id: id}).then((res) => {
            console.log(res)
            this.update_list()
          }).catch((error) => {
              console.log(error)
          })
        },
      update_list: function(){
        axios.get('http://127.0.0.1:5000/api/list').then((res) => {
          this.$store.commit('set_list', res.data.sort(function(a,b) {return a.id - b.id}))
        }).catch((error) => {
          console.log(error);
        })

      },
      add_subtask: function(id, message){
        if (message.length == 0) {
          this.writingSubtask = 0
          this.subtask = ""
        } else {
          axios.post('http://127.0.0.1:5000/api/addsubtask', {id: id, text: message}).then((res) => {
            console.log(res)
            this.writingSubtask = 0
            this.subtask = ""
            this.update_list()
          }).catch((error) => {
            console.log(error)
          })
        }
        },
      delete_todo: function(id){
        axios.post('http://127.0.0.1:5000/api/remove', {id: id}).then((res) =>{
            console.log(res)
            this.update_list()
        }).catch((error) => {
            console.log(error)
        })
      },
      edit_todo: function(id, message){
        if (message.length == 0) {
          this.editing = 0
          this.edit = ""
        } else {
          axios.post('http://127.0.0.1:5000/api/edit', {id: id, text: message}).then((res) =>{
            console.log(res)
            this.editing = 0
            this.edit = ""
            this.update_list()
          }).catch((error) => {
            console.log(error)
          })
        }
      },
      download_export: function(){
        axios.get('http://127.0.0.1:5000/api/export').then((res) =>{
          const blob = new Blob([res.data]);
          const link = document.createElement("a");
          link.href = URL.createObjectURL(blob);
          link.download = "todo_export.csv";
          link.click();
          URL.revokeObjectURL(link.href);
        })
      },
      download_logs: function(){
        axios.get('http://127.0.0.1:5000/api/logs').then((res) =>{
          const blob = new Blob([res.data]);
          const link = document.createElement("a");
          link.href = URL.createObjectURL(blob);
          link.download = "server_logs.txt";
          link.click();
          URL.revokeObjectURL(link.href);
        })
      },
      enable_editing_subtask: function(id){
          this.writingSubtask = id
        },
      enable_editing: function(id, message){
          document.getElementById(id).value = message
          document.getElementById(id).placeholder = message
          this.editing = id
        }
    },
  computed:{
      todos(){
          return this.$store.state.list
        }
    },
  created() {
    this.update_list()
  }
}

</script>
<style lang="scss">
#table-entry {
  padding: 5px;
  max-width:750px
}
</style>
