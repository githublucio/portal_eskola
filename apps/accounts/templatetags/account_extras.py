from django import template

register = template.Library()


@register.filter
def get_field(obj, name):
    if obj is None:
        return "—"
    if name == "full_name" and hasattr(obj, "full_name"):
        return obj.full_name
    if name == "action" and hasattr(obj, "get_action_display"):
        return obj.get_action_display()
    if name == "user":
        value = getattr(obj, "user", None)
        return value or "—"
    if name == "desired_course":
        course = getattr(obj, "desired_course", None)
        if course:
            return str(course)
        return getattr(obj, "desired_course_text", None) or "—"
    display = getattr(obj, f"get_{name}_display", None)
    if callable(display):
        return display()
    value = getattr(obj, name, None)
    if value is None or value == "":
        return "—"
    if hasattr(value, "strftime"):
        return value.strftime("%d-%m-%Y %H:%M")
    if isinstance(value, bool):
        return "Sim" if value else "Lae"
    return value
