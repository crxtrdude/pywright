An ongoing updated list of potentially backwards incompatible changes which we should make in the future. When we are ready to throw the switch, we should be able to update old games with one of these upgrade paths:

  * one or two lines of code thrown into their intro.txt
  * some kind of automated change that I code
  * ensuring that old content is moved into the games zip so it uses old files instead of new

Here's the list:

**Content**
  * Delete art/bg/main, art/bg/main2
  * Rename `art/fg/CrossExamination-Anim`
  * Choose default button layout, ensure each official game sets the right one

**Scripting**
  * change examine from examine,region,region,... to examine,region,region,showexamine
  * remove `_list_back_button` and `_cr_back_button` properties for displaying the back button. Replace with "noback" property. May not be able to automate this change, but we should look for where `_cr_back_button` and `_list_back_button` are set.
  * shake only shakes top screen by default (if someone has used shake in a cutscene, we should change the command to 'shake both')
    * Such as the intro to turnabout scapegoat
  * delete `_bigbutton_bg` (rename to `_screen2_bg`)
  * 'text macros' are moving to just wrightscript commands inside the {}. This only causes problems for a few commands which use a single letter followed by arguments without spaces: 'e', 'f', 's', 'p', 'c'. A converter can easily check these few side characters and add a space.