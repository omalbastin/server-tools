# © 2014 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#        Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# © 2015 Antiun Ingeniería S.L. - Jairo Llopis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models, tools


class Owner(models.AbstractModel):
    _name = "base_multi_image.owner"
    _description = """ Wizard for base multi image """

    image_ids = fields.One2many(
        comodel_name='base_multi_image.image',
        inverse_name='owner_id',
        string='Images',
        domain=lambda self: [("owner_model", "=", self._name)],
        copy=True)
    image_main = fields.Image(
        string="Main image",
        store=False,
        compute="_compute_get_multi_image",
        inverse="_inverse_set_multi_image_main")
    # image_main_medium = fields.Binary(
    #     string="Medium image",
    #     compute="_get_multi_image",
    #     inverse="_set_multi_image_main_medium",
    #     store=False)
    # image_main_small = fields.Binary(
    #     string="Small image",
    #     compute="_get_multi_image",
    #     inverse="_set_multi_image_main_small",
    #     store=False)

    @api.depends('image_ids')
    def _compute_get_multi_image(self):
        """Get the main image for this object.

        This is provided as a compatibility layer for submodels that already
        had one image per record.
        """
        for s in self:
            first = s.image_ids[:1]
            s.image_main = first.image_main
            s.image_1920 = first.image_1920
            # s.image_main_medium = first.image_medium
            # s.image_main_small = first.image_small

    def _set_multi_image(self, image=False, name=False):
        """Save or delete the main image for this record.

        This is provided as a compatibility layer for submodels that already
        had one image per record.
        """
        # Values to save
        multi_image_obj = self.env['base_multi_image.image']
        storage = multi_image_obj.default_get(['storage'])['storage']
        if storage != "db":
            storage = "filestore"
        atts = self.env['ir.attachment'].sudo()

        values = {"storage": storage,
                  "owner_model": self._name,
                  "owner_id": self.id}
        if name:
            values["name"] = name
        image_rec = False
        if self.image_ids:
            image_rec = self.image_ids[0]
        if not image:
            image_rec and image_rec.unlink()
            return True
        if storage == "db":
            values.update({
                "file_db_store": tools.image_resize_image_big(image),
            })
        else:

            if image_rec.storage == 'filestore':
                attachment_id = image_rec.attachment_id
                attachment_id.write({'datas': image})
            else:
                attachment_id = atts.create({
                        # 'name': self.name,
                        'res_model': self._name,
                        # 'res_field': 'image_1920',
                        'res_id': self.id,
                        'type': 'binary',
                        'datas': image,
                    })
                values["attachment_id"] = attachment_id.id

        if image_rec:
            #write
            image_rec.write(values)
        else:
            #create
            values.setdefault("name", name or _("Main image"))
            self.image_ids = [(0, 0, values)]

    def _inverse_set_multi_image_main(self):
        for owner in self:
            owner._set_multi_image(owner.image_main)

    # def _set_multi_image_main_medium(self):
    #     self._set_multi_image(self.image_main_medium)
    #
    # def _set_multi_image_main_small(self):
    #     self._set_multi_image(self.image_main_small)

    def unlink(self):
        """Mimic `ondelete="cascade"` for multi images.

        Will be skipped if ``env.context['bypass_image_removal']`` == True
        """
        images = self.mapped("image_ids")
        result = super(Owner, self).unlink()
        if result and not self.env.context.get('bypass_image_removal'):
            images.unlink()
        return result
