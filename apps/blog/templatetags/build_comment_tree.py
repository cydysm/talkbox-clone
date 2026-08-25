from django import template

register = template.Library()


@register.filter
def build_comment_tree(comments):
    nodes = list(comments)
    lookup = {comment.id: {"comment": comment, "replies": []} for comment in nodes}
    roots = []
    for comment in nodes:
        node = lookup[comment.id]
        if comment.parent_id and comment.parent_id in lookup:
            lookup[comment.parent_id]["replies"].append(node)
        else:
            roots.append(node)
    return roots
