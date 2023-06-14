---
layout: default
title: Development
nav_order: 1
parent: Provena
---

{: .no_toc }

#  Development

<details  open markdown="block">
  <summary>
    Table of contents
  </summary>
{: .text-delta }
* TOC
{:toc}
____
</details>

We are using a Jekyll Site to host documentation, and the 'Just-The-Docs' for theming.

Documentation repository is hosted on Github [here](https://github.com/gbrrestoration/rrap-mds-knowledge-hub)

There are a number of ways to edit/develop the documentation:

-   If making small changes (fixing a spelling error) this can be done within GitHub itself using the local editor
-   If making large/many changes you should clone the repository and make the changes and validate on your local machine prior to pushing back to the repository. After pushing back to the repository the changes will be built and deployed on GitHub → https://gbrrestoration.github.io/rrap-mds-knowledge-hub/
-   If making structure changes or adding complex html elements to be included with the markdown it would be best to have a local environment to build the site. See the repository development.md for steps in setting up your local environment

____

## Local Development Environment setup

### Linux development

Follow the guide [local installation using the gem based theme](https://just-the-docs.github.io/just-the-docs/#local-installation-use-the-gem-based-theme)

Note that the above guide is not very detailed about how to setup ruby. I had to install some extra dependencies on debian/ubuntu - namely

-   build-essential
-   libsqlite3-dev
-   ruby-full
-   ruby-dev

Therefore, a full setup could be:

```
sudo apt install build-essential libsqlite3-dev ruby-full ruby-dev
sudo gem install just-the-docs
```

then to serve the application locally:

```
./serve.sh
```

### Windows development

Use the [Jekyll Windows installer](https://jekyllrb.com/docs/installation/windows/)
There are a number of packages that are not included which you will need to add separately

1. `gem install wdm`
1. `gem install webrick`

____

## Documentation writing/development

Documents are written using [Markdown](https://www.markdownguide.org/cheat-sheet/) syntax

The Jekyll site is built with `jekyll b` and the servered with `jekyll server --config _config_development.yml`, note that we use a specific `config.yml` for development as the theme is local and we include this file in the site.

There are bash scripts called `build.sh` and `serve.sh` which build and serve the site respectively. The serve script sets up auto reload on the files in the build path meaning you can live edit against the built site.

After pushing code back to the repository GitHub actions will build and deploy the site using `config.yml`

See Jekyll [notes](https://jekyllrb.com/docs/usage/) for further documentation on Jekyll usages

____

### Further documentation on Just-The-Docs

[Just the Docs](https://just-the-docs.github.io/just-the-docs/)

____

## [Markdown](https://www.markdownguide.org/)

### External doco
[Cheat sheet](https://www.markdownguide.org/cheat-sheet/)

### Specifics for tables
Markdown tables can become a little difficult to build, so here is a link to a online tool to make the process a little easier, [MD Table builder](https://www.tablesgenerator.com/markdown_tables)

Here is examples of our callouts

<table>
  <tr align=center>
    <th align=center>Raw</th>
    <th align=center>Result</th>
  </tr>
  <tr align=center>
    <td text-align=center>{%raw%}{% include warning.html content="Watch out" %}{%endraw%}</td>
    <td text-align=center>{% include warning.html content="Watch out." %}</td>
  </tr>
  <tr align=center>
    <td>{%raw%}{% include danger.html content="DO NOT ENTER." %}{%endraw%}</td>
    <td>{% include danger.html content="DO NOT ENTER" %}</td>
  </tr>
  <tr align=center>
    <td>{%raw%}{% include success.html content="Well done!" %}{%endraw%}</td>
    <td>{% include success.html content="Well done!" %}</td>
  </tr>
  <tr align=center>
    <td>{%raw%}{% include notes.html content="You can do it" %}{%endraw%}</td>
    <td>{% include notes.html content="You can do it" %}</td>
  </tr>
  <tr align=center>
    <td>{%raw%}{% include notes.html content="You can<b> bold</b> with html tags" %}{%endraw%}</td>
    <td>{% include notes.html content="You can<b> bold</b> with html tags" %}</td>
  </tr>
  <tr>
    <td>Currently the callouts will not except html link tags, so here is a work around <br> &lt;div class="info">&lt;strong>Note!</strong> I would like to hyperlink to another page please, &lt;a href='www.google.com'>go to Google</a>&lt;/div></td>
    <td text-align=center><div class="info"><strong>Note! </strong> I would like to hyperlink to another page please,  <a href='www.google.com'>go to Google</a></div></td>
  </tr> 
</table>

____
### External links example
There are a number of ways to create a hyperlink to either a internal location (heading/anchor), internal page or external site.  Depending on your requirement and target here are a few ways to create the link.
#### Markdown
- **Raw** -> `[link text open in current tab](https://github.com/gbrrestoration/rrap-mds-knowledge-hub)`
  - **Result** -> [link text open in current tab](https://github.com/gbrrestoration/rrap-mds-knowledge-hub)
- **Raw** -> `[link text open in new tab](https://github.com/gbrrestoration/rrap-mds-knowledge-hub){:target="\_blank"}`
  - **Result** -> [link text open in new tab](https://github.com/gbrrestoration/rrap-mds-knowledge-hub){:target="\_blank"}
- **Raw** -> `[local link text open in new tab](./index.html){:target="\_blank"}`
  - **Result** -> [local link text open in new tab](./index.html){:target="\_blank"}
- **Raw** ->`[local link to anchor text open in new tab](./information-system/data-store/dataset-metadata.html#metadata){:target="\_blank"}`
  - **Result** -> [local link to anchor text open in new tab](./information-system/data-store/dataset-metadata.html#metadata){:target="\_blank"}

#### HTML
- **Raw** -> `<a href="https://github.com/gbrrestoration/rrap-mds-knowledge-hub" >link text open in current tab</a>`
  - **Result** -> <a href="https://github.com/gbrrestoration/rrap-mds-knowledge-hub" >link text open in current tab</a>
- **Raw** -> `<a href="https://github.com/gbrrestoration/rrap-mds-knowledge-hub" target="_blank">link text open in new tab</a>`
  - **Result** -> <a href="https://github.com/gbrrestoration/rrap-mds-knowledge-hub" target="_blank">link text open in new tab</a>


#### Jekyll include
- **Raw** -> `{% include external_link.html url="https://gbrrestoration.org/" link_text="link text open in new tab" %}`
  - **Result** -> {% include external_link.html url="https://gbrrestoration.org/" link_text="link text open in new tab" %}

___
## VS Code configuration

### Settings.json

This repo includes a `.vscode` directory which includes local settings for the workspace. These settings can be configured to enable the ideal workspace settings for markdown Jekyll development. Currently they specify intellisense to cooperate with snippets on markdown files, and autosave to occur automatically every 3 seconds.

### Snippets

If you find common markdown patterns you are using frequently, add it as a snippet. Current examples include links to new tabs, and a snippet for each of the above notes, danger and success. Snippets can be activated by typing the 'prefix' phrase, pressing tab or enter to select it, then tabbing between input locations. More info [here](https://code.visualstudio.com/docs/editor/userdefinedsnippets){:target="\_blank"}.

  
