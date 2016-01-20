# Version Control and what I use #

I use mercurial as my source control package. It is a distributed version control system, which keeps track of all of the files for the project. You can make changes to the files, and see a history of every change that you've made, allowing you to go back to an old version if you screw something up. It's also useful for me to compile the changelog for each version, as I just run through the version history and distill everything into understandable bullet points.

# Working with google #

The so-called **main branch** of pywright is hosted here at google code. When I want to work on stuff, I will update my local copy of the code (called a **working copy** or local branch) with any changes from google code. After I am satisfied with a small change, I commit the change to my working copy. I may make several small changes like this while I work on something bigger. Then I **push** all of the changes back to the main branch.

# How to get involved #

If you are going to be modifying code, you'll need a version of mercurial for your operating system. There are command line tools as well as graphical ones. I use TortoiseHG for windows. You can find some of these interfaces here: http://mercurial.selenic.com/wiki/Mercurial. I recommend just mercurial (command line) for linux, tortoisehg for windows, and machg for osx.

# Tutorial #

There are probably better tutorials out there, but this describes what I do. I use tortoisehg in the example, other programs will be different, but the general process is similar.

## Install Mercurial ##

Obviously the first thing to do is to install the edition of mercurial you are going to use.

## Check out code ##

![http://pywright.googlecode.com/files/03_getpassword.jpg](http://pywright.googlecode.com/files/03_getpassword.jpg)

Before we get to work, you will need authentication. If you have a google account, and are registered with the project, you can find your code password by clicking on your profile on this site, and going to settings. You'll need this password later. Note that it is possible to check out the code without an account, you just wont be able to directly send any changes back.

You need to clone the **main branch** into a folder on your computer, to create the **working copy**. All of the changes you make will be in this folder. I put mine in a folder on my desktop called dev/pywright. For tortoisehg, you navigate with explorer to the folder where the working copy will end up; other programs may have you find this folder in the program itself.

![http://pywright.googlecode.com/files/01_starttortoise.jpg](http://pywright.googlecode.com/files/01_starttortoise.jpg)

**I navigate to the folder to put my working copy, right click, and go to the tortoisehg selector...**

![http://pywright.googlecode.com/files/02_clone.jpg](http://pywright.googlecode.com/files/02_clone.jpg)

**Then I choose the clone option**

![http://pywright.googlecode.com/files/04_enter_username_key.jpg](http://pywright.googlecode.com/files/04_enter_username_key.jpg)

The url to enter for the "source" of the clone will be https://user%40gmail.com:password@pywright.googlecode.com/hg/ where password is replaced with the password we got at the beginning, and user is your google username. This way when you make changes, google code will remember who changed what, and let you send changes without asking for a password every time.

The "destination" path is where the working copy will be placed, and where you will work on the files. The other options on this screen are not important.

![http://pywright.googlecode.com/files/05_run_clone.jpg](http://pywright.googlecode.com/files/05_run_clone.jpg)

The files will download, and as there are a lot of images and sound files, it may take a while. It's downloading not only the files themselves, but the history of all the changes made to those files since I started working in mercurial. I'd estimate about 300 mb. When updating the code after the first clone, it will be much faster, because you ONLY download the changes.

![http://pywright.googlecode.com/files/06_editchangelog.jpg](http://pywright.googlecode.com/files/06_editchangelog.jpg)

Now that I have the files downloaded, I'm going to make a simple change. Let's say I want to add some text into the changelog.

![http://pywright.googlecode.com/files/07_editchangelog.jpg](http://pywright.googlecode.com/files/07_editchangelog.jpg)

Here I added a line about something that I did in another change. Next we need to tell version control to save this change.

![http://pywright.googlecode.com/files/08_changed_changelog.jpg](http://pywright.googlecode.com/files/08_changed_changelog.jpg)

Notice that mercurial is letting me know that this is a new change that has not been recorded, by putting a red exclamation on the file. Now I need to **commit** the file, which is the term for telling version control to remember the change.

![http://pywright.googlecode.com/files/09_viewrepo.jpg](http://pywright.googlecode.com/files/09_viewrepo.jpg)

![http://pywright.googlecode.com/files/10_commit.jpg](http://pywright.googlecode.com/files/10_commit.jpg)

(A)I need to write a message describing what kind of change I made. This is not optional. In (B) I am shown the exact change, minus means a line was removed, plus means a line was added. It's a good way to preview your change and make sure it is correct. In (C) I make sure to tell mercurial which files I actually want to save at this time. In this case it's showing me some other files that aren't recorded at all (the files or the changes to them). There are files that we DON'T want to save to versions, such as log files, or local pywright settings.

When I am ready, I click the commit button (D), and wait for it to finish. Since it is only recording changes locally, to the working copy, it is fast.

![http://pywright.googlecode.com/files/11_commit_dialog.jpg](http://pywright.googlecode.com/files/11_commit_dialog.jpg)

Next we **push**. This will send all of the changes that are new to the **main branch** to google. No one except you will see the changes until you do this step. Also, this will only work if your account is authenticated. In tortoisehg the icon is a green up arrow with a line above it. The green up arrow without a line will show you which changes are going to be pushed.

![http://pywright.googlecode.com/files/12_about_to_push.jpg](http://pywright.googlecode.com/files/12_about_to_push.jpg)

It asks you again if you are sure. Click push.

![http://pywright.googlecode.com/files/13_push.jpg](http://pywright.googlecode.com/files/13_push.jpg)

It's slower than commit, but still pretty fast, since it only uploads the exact lines that you added. If you are adding files like graphics, or music, it will take longer.

Another concept is **pull**. The green down arrow in tortoise will show us any new changesets - modifications to the files that exist on the main branch that you don't have yet. In this case, I am on another computer and able to see the changelog modification I had pushed.

A **pull** will download the changes to your computer, but not actually make the changes to your working copy. **update** will unpack these changes, and make your working copy identical to the **main branch**

There are convenience functions to pull and update at the same time, since usually you are going to do both.

![http://pywright.googlecode.com/files/14_incoming.jpg](http://pywright.googlecode.com/files/14_incoming.jpg)