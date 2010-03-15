'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Frank Niessink <frank@niessink.com>

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

itemImagePlural = dict(book_icon='books_icon',
                       cogwheel_icon='cogwheels_icon',
                       envelope_icon='envelopes_icon',
                       heart_icon='hearts_icon',
                       key_icon='keys_icon',
                       led_blue_icon='folder_blue_icon',
                       led_blue_light_icon='folder_blue_light_icon',
                       led_grey_icon='folder_grey_icon',
                       led_green_icon='folder_green_icon',
                       led_green_light_icon='folder_green_light_icon',
                       led_orange_icon='folder_orange_icon',
                       led_purple_icon='folder_purple_icon',
                       led_red_icon='folder_red_icon',
                       led_yellow_icon='folder_yellow_icon',
                       person_icon='persons_icon')


itemImageSingular = dict()
for key, value in itemImagePlural.iteritems():
    itemImageSingular[value] = key