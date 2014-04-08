"""
Created on 26.02.2014

@author: jpi
"""

from django.utils.translation import ugettext as _
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver


class ItemWithMedia(models.Model):
    """
    Superclass to distinguish between the different media-using objects
    """
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modified = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __unicode__(self):
        try:
            return self.entrytype.__unicode__()
        except ObjectDoesNotExist:
            try:
                return self.location.__unicode__()
            except ObjectDoesNotExist:
                try:
                    return self.entry.__unicode__()
                except ObjectDoesNotExist:
                    return self.id


class EntryType(ItemWithMedia):
    """
    List of types a new entry can be
    """
    label = models.CharField(max_length=25)

    def __unicode__(self):
        return self.label


class Location(ItemWithMedia):
    """
    A Location with a geoposition
    """
    label = models.CharField(max_length=150)
    latitude = models.DecimalField(decimal_places=15, max_digits=18)
    longitude = models.DecimalField(decimal_places=15, max_digits=18)
    dbpedia_link = models.CharField(max_length=500, null=True, blank=True)

    def __unicode__(self):
        return self.label + " [" + str(self.latitude) + ", " + str(self.longitude) + "]"


class Entry(ItemWithMedia):
    """
    One entry
    """
    type = models.ForeignKey(EntryType, on_delete=models.PROTECT)
    title = models.CharField(max_length=150)
    abstract = models.TextField()
    text = models.TextField(null=True, blank=True)
    author = models.CharField(max_length=150)
    time_start = models.DateField()
    time_end = models.DateField(null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)

    def __unicode__(self):
        return self.title + " (" + self.author + ")"


class MediaObject(models.Model):
    """
    Media Object to save images, videos or audio files that belong to an entry,
    a location or an entry type
    """
    VIDEO = "vid"
    IMAGE = "img"
    SOUND = "aud"
    MEDIA_TYPES = (
        (VIDEO, _("Video")),
        (IMAGE, _("Bild")),
        (SOUND, _("Audio")),
    )
    entry = models.ForeignKey(ItemWithMedia)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modified = models.DateTimeField(auto_now=True, null=True, blank=True)
    type = models.CharField(max_length=3, choices=MEDIA_TYPES, default=IMAGE)
    alt = models.CharField(max_length=300)

    def __unicode__(self):
        entry_name = " (" + self.entry.__unicode__() + ")"
        return self.alt + entry_name


class MediaSource(models.Model):
    """
    One Source file that belongs to a media object
    """

    def get_upload_path(self, filename):
        return str(self.media_object.entry.id) + "/" + filename

    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modified = models.DateTimeField(auto_now=True, null=True, blank=True)
    media_object = models.ForeignKey(MediaObject)
    file = models.FileField(upload_to=get_upload_path)

    def __unicode__(self):
        return self.file.name

@receiver(post_delete, sender=MediaSource)
def delete_file(sender, instance, **kwargs):
    if instance.file is not None:
        instance.file.delete(False)