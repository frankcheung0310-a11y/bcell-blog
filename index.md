---
layout: default
---
# B-Cell AI: Intelligence Behind the Immunity

Exploring Generative AI in B-cell Biology and Antibody Discovery.

## 📢 Industry Feed
<ul>
  {% for post in site.posts %}
    <li>
      <a href="{{ post.url }}">{{ post.title }}</a> - {{ post.date | date: "%Y-%m-%d" }}
    </li>
  {% endfor %}
</ul>
