from .Nodz import nodz_main
from .Nodz import nodz_utils
from Qt import QtGui
from Qt import QtCore


class Graph(nodz_main.Nodz):
    def __init__(self, model, parent=None):
        self.__model = model
        super(Graph, self).__init__(parent)

    def boxModel(self):
        return self.__model

    def addBlock(self, blockName):
        bloc = self.__model.addBlock(blockName)
        if bloc:
            # TODO : set position QtGui.QCursor.pos()
            node = self.createNode(bloc, position=None)

            # TODO : preset
            for ip in bloc.inputs():
                self.createAttribute(node=node, port=ip, plug=False, socket=True, preset="attr_preset_1", dataType=ip.typeClass())

            for op in bloc.outputs():
                self.createAttribute(node=node, port=op, plug=True, socket=False, preset="attr_preset_1", dataType=op.typeClass())

    def createNode(self, bloc, preset='node_default', position=None, alternate=True):
        if bloc.name() in self.scene().nodes.keys():
            print('A node with the same name already exists : {0}'.format(bloc.name()))
            print('Node creation aborted !')
            return

        nodeItem = BlocItem(bloc, alternate, preset, self.config)

        # Store node in scene.
        self.scene().nodes[bloc.name()] = nodeItem

        if not position:
            # Get the center of the view.
            position = self.mapToScene(self.viewport().rect().center())

        # Set node position.
        self.scene().addItem(nodeItem)
        nodeItem.setPos(position - nodeItem.nodeCenter)

        # Emit signal.
        self.signal_NodeCreated.emit(bloc.name())

        return nodeItem

    def createAttribute(self, node, port, index=-1, preset='attr_default', plug=True, socket=True, dataType=None):
        if not node in self.scene().nodes.values():
            print('Node object does not exist !')
            print('Attribute creation aborted !')
            return

        if port.name() in node.attrs:
            print('An attribute with the same name already exists : {0}'.format(port.name()))
            print('Attribute creation aborted !')
            return

        node._createAttribute(port, index=index, preset=preset, plug=plug, socket=socket, dataType=dataType)

        # Emit signal.
        self.signal_AttrCreated.emit(node.name, index)


class BlocItem(nodz_main.NodeItem):
    def __init__(self, node, alternate, preset, config):
        super(BlocItem, self).__init__(node.name(), alternate, preset, config)
        self.__node = node

    def _createAttribute(self, port, index, preset, plug, socket, dataType):
        if port in self.attrs:
            print('An attribute with the same name already exists on this node : {0}'.format(port))
            print('Attribute creation aborted !')
            return

        self.attrPreset = preset

        if plug:
            plugInst = OutputPort(parent=self,
                                port=port,
                                index=self.attrCount,
                                preset=preset,
                                dataType=dataType)

            self.plugs[port.name()] = plugInst

        if socket:
            socketInst = InputPort(parent=self,
                                    port=port,
                                    index=self.attrCount,
                                    preset=preset,
                                    dataType=dataType)

            self.sockets[port] = socketInst

        self.attrCount += 1

        if index == -1 or index > self.attrCount:
            self.attrs.append(port.name())
        else:
            self.attrs.insert(index, port.name())

        self.attrsData[port.name()] = {'name': port.name(),
                                       'port': port,
                                       'socket': socket,
                                       'plug': plug,
                                       'preset': preset,
                                       'dataType': dataType}

        self.update()

    def paint(self, painter, option, widget):
        """
        Paint the node and attributes.

        """
        # Node base.
        painter.setBrush(self._brush)
        painter.setPen(self.pen)

        painter.drawRoundedRect(0, 0,
                                self.baseWidth,
                                self.height,
                                self.radius,
                                self.radius)

        # Node label.
        painter.setPen(self._textPen)
        painter.setFont(self._nodeTextFont)

        metrics = QtGui.QFontMetrics(painter.font())
        text_width = metrics.boundingRect(self.name).width() + 14
        text_height = metrics.boundingRect(self.name).height() + 14
        margin = (text_width - self.baseWidth) * 0.5
        textRect = QtCore.QRect(-margin,
                                -text_height,
                                text_width,
                                text_height)

        painter.drawText(textRect,
                         QtCore.Qt.AlignCenter,
                         self.name)


        # Attributes.
        offset = 0
        for attr in self.attrs:
            nodzInst = self.scene().views()[0]
            config = nodzInst.config

            # Attribute rect.
            rect = QtCore.QRect(self.border / 2,
                                self.baseHeight - self.radius + offset,
                                self.baseWidth - self.border,
                                self.attrHeight)



            attrData = self.attrsData[attr]
            name = attr

            preset = attrData['preset']


            # Attribute base.
            self._attrBrush.setColor(nodz_utils._convertDataToColor(config[preset]['bg']))
            if self.alternate:
                self._attrBrushAlt.setColor(nodz_utils._convertDataToColor(config[preset]['bg'], True, config['alternate_value']))

            self._attrPen.setColor(nodz_utils._convertDataToColor([0, 0, 0, 0]))
            painter.setPen(self._attrPen)
            painter.setBrush(self._attrBrush)
            if (offset / self.attrHeight) % 2:
                painter.setBrush(self._attrBrushAlt)

            painter.drawRect(rect)

            # Attribute label.
            painter.setPen(nodz_utils._convertDataToColor(config[preset]['text']))
            painter.setFont(self._attrTextFont)

            # Search non-connectable attributes.
            if nodzInst.drawingConnection:
                if self == nodzInst.currentHoveredNode:
                    port = attrData['port']
                    if (nodzInst.sourceSlot.slotType == 'plug' and attrData['socket'] == False) or (nodzInst.sourceSlot.slotType == 'socket' and attrData['plug'] == False):
                        # Set non-connectable attributes color.
                        painter.setPen(nodz_utils._convertDataToColor(config['non_connectable_color']))

            textRect = QtCore.QRect(rect.left() + self.radius,
                                     rect.top(),
                                     rect.width() - 2*self.radius,
                                     rect.height())
            painter.drawText(textRect, QtCore.Qt.AlignVCenter, name)

            offset += self.attrHeight


class OutputPort(nodz_main.PlugItem):
    def __init__(self, parent, port, index, preset, dataType):
        super(OutputPort, self).__init__(parent, port.name(), index, preset, dataType)
        self.__port = port

    def port(self):
        return self.__port

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setPen(self.pen)

        nodzInst = self.scene().views()[0]
        config = nodzInst.config
        if nodzInst.drawingConnection:
            if self.parentItem() == nodzInst.currentHoveredNode:
                painter.setBrush(nodz_utils._convertDataToColor(config['non_connectable_color']))
                if (self.slotType == nodzInst.sourceSlot.slotType or (self.slotType != nodzInst.sourceSlot.slotType and not nodzInst.sourceSlot.port().match(self.port()))):
                    painter.setBrush(nodz_utils._convertDataToColor(config['non_connectable_color']))
                else:
                    _penValid = QtGui.QPen()
                    _penValid.setStyle(QtCore.Qt.SolidLine)
                    _penValid.setWidth(2)
                    _penValid.setColor(QtGui.QColor(255, 255, 255, 255))
                    painter.setPen(_penValid)
                    painter.setBrush(self.brush)

        painter.drawEllipse(self.boundingRect())

    def accepts(self, socket_item):
        if isinstance(socket_item, nodz_main.SocketItem):
            if self.parentItem() != socket_item.parentItem():
                if socket_item.port().match(self.port()):
                    if socket_item in self.connected_slots:
                        return False
                    else:
                        return True
            else:
                return False
        else:
            return False


class InputPort(nodz_main.SocketItem):
    def __init__(self, parent, port, index, preset, dataType):
        super(InputPort, self).__init__(parent, port.name(), index, preset, dataType)
        self.__port = port

    def port(self):
        return self.__port

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setPen(self.pen)

        nodzInst = self.scene().views()[0]
        config = nodzInst.config
        if nodzInst.drawingConnection:
            if self.parentItem() == nodzInst.currentHoveredNode:
                painter.setBrush(nodz_utils._convertDataToColor(config['non_connectable_color']))
                if (self.slotType == nodzInst.sourceSlot.slotType or (self.slotType != nodzInst.sourceSlot.slotType and not self.port().match(nodzInst.sourceSlot.port()))):
                    painter.setBrush(nodz_utils._convertDataToColor(config['non_connectable_color']))
                else:
                    _penValid = QtGui.QPen()
                    _penValid.setStyle(QtCore.Qt.SolidLine)
                    _penValid.setWidth(2)
                    _penValid.setColor(QtGui.QColor(255, 255, 255, 255))
                    painter.setPen(_penValid)
                    painter.setBrush(self.brush)

        painter.drawEllipse(self.boundingRect())

    def accepts(self, plug_item):
        if isinstance(plug_item, nodz_main.PlugItem):
            if (self.parentItem() != plug_item.parentItem() and
                len(self.connected_slots) <= 1):
                if self.port().match(plug_item.port()):
                    if plug_item in self.connected_slots:
                        return False
                    else:
                        return True
            else:
                return False
        else:
            return False
