#-*- coding: utf-8 -*-

import background


def bg(daemon=True):
    """
    Alias for background(daemon=True)
    """

    return background.background(daemon)
