<template>
    <transition name="modal">
        <div class="modal-mask">
        <div class="modal-wrapper">
            <div class="modal-container text-center">

              <div class="modal-header text-center">
                  <slot name="header">
                  Gallery Snippet
                  </slot>
              </div>

              <div class="modal-body">
                  <textarea id="embedId" rows="5" style="resize: none" :value="embed">
                  </textarea>
              </div>

              <div class="modal-footer">
                <p-button type="primary" @click.native="copyEmbed" class="btn-block">Copy to clipboard
                </p-button>
              </div>
            </div>
        </div>
        </div>
    </transition>
</template>


<script>
import Button from "./Button.vue";

export default {
    name: 'modal',
    props: {
        embed: String
    },
    methods: {
        copyEmbed() {
            this.$emit('close');
            let embedString = document.querySelector('#embedId')
            embedString.setAttribute('type','text')
            embedString.select()
            try {
                var successful = document.execCommand('copy');
                var msg = successful ? 'successfully' : 'unsuccessfully';
                // alert('Code copied ' + msg);
            } 
            catch (err) {
                alert('Unable to copy ' + msg);                
            }

            /* unselect the range */
            embedString.setAttribute('type', 'hidden')
            window.getSelection().removeAllRanges()
        }
    }
}
</script>


<style>

.modal-mask {
  position: fixed;
  z-index: 9998;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, .5);
  display: table;
  transition: opacity .3s ease;
}

.modal-wrapper {
  display: table-cell;
  vertical-align: middle;
}

.modal-container {
  width: 300px;
  margin: 0px auto;
  padding: 20px 30px;
  background-color: #fff;
  border-radius: 2px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, .33);
  transition: all .3s ease;
  font-family: Helvetica, Arial, sans-serif;
}

.modal-header h3 {
  margin-top: 0;
  color: #42b983;
}

.modal-body {
  margin: 20px 0;
}


/*
 * The following styles are auto-applied to elements with
 * transition="modal" when their visibility is toggled
 * by Vue.js.
 *
 * You can easily play with the modal transition by editing
 * these styles.
 */

.modal-enter {
  opacity: 0;
}

.modal-leave-active {
  opacity: 0;
}

.modal-enter .modal-container,
.modal-leave-active .modal-container {
  -webkit-transform: scale(1.1);
  transform: scale(1.1);
}

</style>
