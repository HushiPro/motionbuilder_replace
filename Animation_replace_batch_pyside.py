#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MotionBuilder 2019 动画替换批处理脚本 - PySide2版本
适用于Python 2.7
功能：批量处理FBX文件，替换动画数据
"""

import os
import sys
import time
from pyfbsdk import *
from pyfbsdk_additions import *

# 导入PySide2
try:
    from PySide2.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                                   QLabel, QLineEdit, QPushButton, QTextEdit, 
                                   QFileDialog, QMessageBox, QProgressBar, QGroupBox)
    from PySide2.QtCore import Qt
    from PySide2.QtGui import QFont
except ImportError:
    print("错误：无法导入PySide2，请确保已安装PySide2")
    sys.exit(1)


class BatchProcessor:
    """批处理器 - 单线程版本"""
    
    def __init__(self, source_path, hik_path, save_path, current_character, log_callback):
        self.source_path = source_path
        self.hik_path = hik_path
        self.save_path = save_path
        self.current_character = current_character
        self.log_callback = log_callback  # 日志回调函数
        self.is_running = True
        
    def stop(self):
        self.is_running = False
        
    def ensure_str(self, path):
        """确保路径是str类型，不是unicode（Python 2.7兼容）"""
        if isinstance(path, unicode):
            return str(path)
        return path
        
    def log(self, message):
        """统一的日志方法"""
        print(message)  # 输出到控制台
        if self.log_callback:
            self.log_callback(message)  # 通过回调发送到UI
        
    def run(self):
        """运行批处理"""
        try:
            self.log("=== 批处理开始 ===")
            self.log("线程初始化完成，开始处理...")
            self.log("源路径: {}".format(self.source_path))
            self.log("HIK路径: {}".format(self.hik_path))
            self.log("保存路径: {}".format(self.save_path))
            self.log("角色: {}".format(self.current_character))
            
            self.log("=== 开始批处理 ===")
            
            # 获取所有FBX文件
            fbx_files = self.get_fbx_files(self.source_path)
            self.log("扫描源目录: {}".format(self.source_path))
            self.log("找到FBX文件数量: {}".format(len(fbx_files)))
            
            # 立即发送找到的文件列表
            if fbx_files:
                self.log("找到的FBX文件:")
                for i, fbx_file in enumerate(fbx_files):
                    if i < 5:  # 只显示前5个文件
                        self.log("  - {}".format(os.path.basename(fbx_file)))
                    elif i == 5:
                        self.log("  - ... (还有{}个文件)".format(len(fbx_files) - 5))
                        break
            
            if not fbx_files:
                self.log("错误：在指定目录中没有找到FBX文件")
                return False, "在指定目录中没有找到FBX文件"
            
            # 获取HIK文件列表
            hik_files = []
            for root, dirs, files in os.walk(self.hik_path):
                for file in files:
                    if file.lower().endswith('.fbx'):
                        hik_files.append(os.path.join(root, file))
            
            self.log("扫描HIK目录: {}".format(self.hik_path))
            self.log("找到HIK文件数量: {}".format(len(hik_files)))
            
            # 验证HIK文件
            valid_hik_files = self.validate_hik_files(hik_files)
            self.log("有效HIK文件数量: {}".format(len(valid_hik_files)))
            
            if not valid_hik_files:
                return False, "没有找到有效的HIK FBX文件"
            
            # 开始批处理
            total_files = len(fbx_files)
            success_count = 0
            error_count = 0
            
            for i, fbx_file in enumerate(fbx_files):
                if not self.is_running:
                    self.log("批处理被中止")
                    break
                    
                try:
                    self.log("\n--- 处理文件 {}/{} ---".format(i+1, total_files))
                    self.log("文件: {}".format(fbx_file))
                    
                    # 处理单个文件
                    result = self.process_single_file(fbx_file, valid_hik_files[0])
                    if result:
                        success_count += 1
                        self.log("文件处理成功")
                    else:
                        error_count += 1
                        self.log("文件处理失败")
                    
                except Exception as e:
                    error_count += 1
                    error_msg = "错误: 处理文件 {} 时出错 - {}".format(os.path.basename(fbx_file), str(e))
                    self.log("处理文件异常: {}".format(str(e)))
                    import traceback
                    # 获取完整的异常信息
                    exc_info = traceback.format_exc()
                    self.log("异常详情: {}".format(exc_info))
                    continue
            
            final_msg = "批处理完成！成功: {}, 失败: {}".format(success_count, error_count)
            self.log("\n=== 批处理结束 ===")
            self.log(final_msg)
            return True, final_msg
            
        except Exception as e:
            error_msg = "批处理过程中出错: {}".format(str(e))
            self.log("批处理主线程异常: {}".format(str(e)))
            import traceback
            # 获取完整的异常信息
            exc_info = traceback.format_exc()
            self.log("主线程异常详情: {}".format(exc_info))
            return False, error_msg
    
    def get_fbx_files(self, directory):
        """获取目录下的所有FBX文件"""
        fbx_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.fbx'):
                    fbx_files.append(os.path.join(root, file))
        return fbx_files
    
    def validate_hik_files(self, hik_files):
        """验证HIK文件列表，只返回有效的FBX文件"""
        valid_files = []
        for hik_file in hik_files:
            try:
                if (os.path.exists(hik_file) and os.path.isfile(hik_file) and 
                    os.path.getsize(hik_file) > 0 and hik_file.lower().endswith('.fbx')):
                    valid_files.append(hik_file)
            except:
                pass
        return valid_files
    
    def process_single_file(self, fbx_file, hik_file):
        """处理单个FBX文件"""
        try:
            # 确保文件路径是str类型，不是unicode
            fbx_file = self.ensure_str(fbx_file)
            hik_file = self.ensure_str(hik_file)
            
            self.log("  -> 打开源FBX文件...")
            # 打开源FBX文件
            if not FBApplication().FileOpen(fbx_file):
                self.log("  -> 打开源FBX文件失败")
                return False
            self.log("  -> 源FBX文件打开成功")
 
            # 打开后先将动画Plot到Control Rig
            try:
                self.log("  -> 准备将动画Plot到Control Rig...")
                character = FBApplication().CurrentCharacter
                if not character:
                    # 备用：从场景中查找第一个FBCharacter
                    self.log("    --> 当前未设置CurrentCharacter，尝试从场景中查找角色...")
                    for comp in FBSystem().Scene.Components:
                        if comp.ClassName() == 'FBCharacter':
                            character = comp
                            break
                if not character:
                    self.log("    --> 未找到角色，无法Plot到Control Rig")
                else:
                    self.log("    --> 使用角色: {}".format(character.Name))
                    # 确保角色已Characterize
                    if not character.GetCharacterize():
                        self.log("    --> 角色未Characterize，执行Characterize...")
                        character.SetCharacterizeOn(True)
                    # 确保存在Control Rig
                    if not getattr(character, 'ControlRig', None):
                        self.log("    --> 未检测到Control Rig，自动创建...")
                        character.CreateControlRig(True)
                        self.log("    --> Control Rig创建完成")
                    # Plot到Control Rig
                    plot_options = FBPlotOptions()
                    plot_options.ConstantKeyReducerKeepOneKey = True
                    plot_options.PlotAllTakes = False
                    plot_options.PlotTranslationOnRootOnly = True
                    plot_result = character.PlotAnimation(FBCharacterPlotWhere.kFBCharacterPlotOnControlRig, plot_options)
                    self.log("    --> Plot到Control Rig结果: {}".format(plot_result))
            except Exception as e:
                self.log("    --> Plot到Control Rig异常: {}".format(str(e)))

            self.log("  -> 保存角色动画...")
            # 保存角色动画
            anim_file = self.save_character_animation(fbx_file)
            if not anim_file:
                self.log("  -> 保存角色动画失败")
                return False
            self.log("  -> 角色动画保存成功: {}".format(anim_file))
            
            self.log("  -> 创建新场景...")
            # 创建新场景
            FBApplication().FileNew()
            self.log("  -> 新场景创建成功")
            
            self.log("  -> 导入HIK文件: {}".format(os.path.basename(hik_file)))
            # 合并HIK文件到当前场景
            # 静默合并，避免弹出merge选项框
            if not FBApplication().FileAppend(hik_file, False):
                self.log("  -> HIK文件合并失败")
                return False
            self.log("  -> HIK文件合并成功")
            
            self.log("  -> 加载角色动画...")
            # 使用Character Controls的Load Character Animation方式
            system = FBSystem()
            character = FBApplication().CurrentCharacter  # 修复：使用FBApplication()
            
            # 确保动画文件路径是str类型
            anim_file = self.ensure_str(anim_file)
            
            self.log("    --> 检查加载时的CurrentCharacter...")
            if character:
                self.log("    --> 找到Character: {}".format(character.Name))
                try:
                    # 使用正确的MotionBuilder API加载角色动画
                    self.log("    --> 使用官方API: FBApplication().LoadAnimationOnCharacter...")
                    
                    # 设置FBX选项 - 按照官方文档
                    fbx_options = FBFbxOptions(True)
                    fbx_options.TransferMethod = FBCharacterLoadAnimationMethod.kFBCharacterLoadCopy
                    fbx_options.ProcessAnimationOnExtension = False
                    fbx_options.ShowOptionsDialog = False  # 禁用弹窗
                    fbx_options.ShowFileDialog = False     # 禁用文件对话框
                    
                    # 设置Plot选项
                    plot_options = FBPlotOptions()
                    
                    # 加载动画到角色 - 官方API方法
                    load_result = FBApplication().LoadAnimationOnCharacter(anim_file, character, fbx_options, plot_options)
                    self.log("    --> LoadAnimationOnCharacter结果: {}".format(load_result))
                    
                    if load_result:
                        self.log("  -> 成功使用官方API加载角色动画")
                    else:
                        self.log("  -> 官方API加载失败")
                        return False
                        
                except Exception as e:
                    self.log("  -> 加载角色动画异常: {}".format(str(e)))
                    import traceback
                    # 获取完整的异常信息
                    exc_info = traceback.format_exc()
                    self.log("加载动画异常详情: {}".format(exc_info))
                    return False
            else:
                self.log("  -> 没有找到有效的CurrentCharacter")
                return False
            
            self.log("  -> 保存最终场景...")
            # 保存场景
            base_name = os.path.splitext(os.path.basename(fbx_file))[0]
            save_file = os.path.join(self.save_path, "{}.fbx".format(base_name))
            # 确保保存路径是str类型
            save_file = self.ensure_str(save_file)
            if not FBApplication().FileSave(save_file):
                self.log("  -> 保存最终场景失败")
                return False
            self.log("  -> 最终场景保存成功: {}".format(save_file))
            
            return True
            
        except Exception as e:
            self.log("  -> process_single_file异常: {}".format(str(e)))
            import traceback
            # 获取完整的异常信息
            exc_info = traceback.format_exc()
            self.log("process_single_file异常详情: {}".format(exc_info))
            return False
    
    def save_character_animation(self, fbx_file):
        """保存角色动画到桌面/Animation目录 """
        # 确保文件路径是str类型
        fbx_file = self.ensure_str(fbx_file)
        
        self.log("    --> 开始保存角色动画...")
        
        # 创建桌面/Animation目录
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        animation_dir = os.path.join(desktop_path, "Animation")
        
        if not os.path.exists(animation_dir):
            os.makedirs(animation_dir)
            self.log("    --> 创建动画目录: {}".format(animation_dir))
        
        # 获取文件名（不含扩展名）
        base_name = os.path.splitext(os.path.basename(fbx_file))[0]
        anim_file = os.path.join(animation_dir, "{}.fbx".format(base_name))
        # 确保动画文件路径是str类型
        anim_file = self.ensure_str(anim_file)
        self.log("    --> 目标动画文件: {}".format(anim_file))
        
        try:
            # 获取/修复当前角色
            target_rigged_character = FBApplication().CurrentCharacter
            if not target_rigged_character:
                self.log("    --> 未检测到CurrentCharacter，尝试从场景中定位角色...")
                chosen_char = None
                # 优先用UI中记录的名称
                try:
                    if hasattr(self, 'current_character') and self.current_character:
                        for comp in FBSystem().Scene.Components:
                            if comp.ClassName() == 'FBCharacter' and comp.Name == self.current_character:
                                chosen_char = comp
                                break
                except Exception:
                    pass
                # 其次选择场景中的第一个FBCharacter
                if not chosen_char:
                    for comp in FBSystem().Scene.Components:
                        if comp.ClassName() == 'FBCharacter':
                            chosen_char = comp
                            break
                # 设置为CurrentCharacter
                if chosen_char:
                    FBApplication().CurrentCharacter = chosen_char
                    target_rigged_character = chosen_char
                    self.log("    --> 已设置CurrentCharacter为: {}".format(chosen_char.Name))
                else:
                    self.log("    --> 错误：场景中未找到任何FBCharacter")
                    return None
             
            self.log("    --> 找到角色: {}".format(target_rigged_character.Name))
             
            # 设置FBX选项用于保存
            fbx_options_save = FBFbxOptions(False)
            fbx_options_save.SetAll(FBElementAction.kFBElementActionSave, True)
             
            # 使用SaveCharacterRigAndAnimation保存角色动画和装备
            self.log("    --> 使用SaveCharacterRigAndAnimation保存...")
            save_result = FBApplication().SaveCharacterRigAndAnimation(
                os.path.normpath(anim_file),
                target_rigged_character,
                fbx_options_save
            )
            
            if save_result:
                self.log("    --> 成功保存角色动画到: {}".format(anim_file))
                # 验证文件是否真的创建了
                if os.path.exists(anim_file):
                    file_size = os.path.getsize(anim_file)
                    self.log("    --> 文件大小: {} bytes".format(file_size))
                    return anim_file
                else:
                    self.log("    --> 错误：文件没有被创建")
                    return None
            else:
                self.log("    --> 错误：SaveCharacterRigAndAnimation返回False")
                return None
                
        except Exception as e:
            self.log("    --> 保存角色动画异常: {}".format(str(e)))
            import traceback
            exc_info = traceback.format_exc()
            self.log("保存动画异常详情: {}".format(exc_info))
            return None


class AnimationReplaceBatchUI(QWidget):
    """动画替换批处理UI"""
    
    def __init__(self):
        super(AnimationReplaceBatchUI, self).__init__()
        self.source_path = ""
        self.hik_path = ""
        self.save_path = ""
        self.current_character = ""
        self.batch_processor = None
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("动画替换批处理工具")
        self.setFixedSize(500, 400)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("动画替换批处理工具")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 当前角色组
        character_group = QGroupBox("当前场景角色")
        character_layout = QHBoxLayout()
        
        self.character_input = QLineEdit()
        self.character_input.setPlaceholderText("未选择")
        self.character_input.setReadOnly(True)
        
        self.character_button = QPushButton("获取角色")
        self.character_button.clicked.connect(self.get_current_character)
        
        character_layout.addWidget(self.character_input)
        character_layout.addWidget(self.character_button)
        character_group.setLayout(character_layout)
        main_layout.addWidget(character_group)
        
        # 路径选择组
        paths_group = QGroupBox("路径设置")
        paths_layout = QVBoxLayout()
        
        # 源数据路径
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("源数据目录:"))
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("选择包含源FBX文件的目录")
        self.source_button = QPushButton("浏览")
        self.source_button.clicked.connect(self.select_source_path)
        
        source_layout.addWidget(self.source_input)
        source_layout.addWidget(self.source_button)
        paths_layout.addLayout(source_layout)
        
        # HIK文件路径
        hik_layout = QHBoxLayout()
        hik_layout.addWidget(QLabel("HIK文件目录:"))
        self.hik_input = QLineEdit()
        self.hik_input.setPlaceholderText("选择包含HIK文件的目录")
        self.hik_button = QPushButton("浏览")
        self.hik_button.clicked.connect(self.select_hik_path)
        
        hik_layout.addWidget(self.hik_input)
        hik_layout.addWidget(self.hik_button)
        paths_layout.addLayout(hik_layout)
        
        # 保存路径
        save_layout = QHBoxLayout()
        save_layout.addWidget(QLabel("保存位置:"))
        self.save_input = QLineEdit()
        self.save_input.setPlaceholderText("选择输出文件的保存位置")
        self.save_button = QPushButton("浏览")
        self.save_button.clicked.connect(self.select_save_path)
        
        save_layout.addWidget(self.save_input)
        save_layout.addWidget(self.save_button)
        paths_layout.addLayout(save_layout)
        
        paths_group.setLayout(paths_layout)
        main_layout.addWidget(paths_group)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("开始批处理")
        self.start_button.clicked.connect(self.start_batch_process)
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_batch_process)
        self.stop_button.setEnabled(False)
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        main_layout.addLayout(control_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        main_layout.addWidget(self.status_label)
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setPlaceholderText("处理日志将显示在这里...")
        main_layout.addWidget(self.log_text)
        
        self.setLayout(main_layout)
        
        # 测试日志系统
        self.log("UI初始化完成 - 日志系统正常工作")
        
    def get_current_character(self):
        """获取当前场景中的角色"""
        self.log("=== 开始获取当前角色 ===")
        try:
            # 使用CurrentActor来获取当前角色
            current_actor = FBApplication().CurrentActor
            self.log("检查CurrentActor...")
            
            if current_actor:
                char_name = current_actor.Name
                self.character_input.setText(char_name)
                self.current_character = char_name
                self.log("成功获取角色: {}".format(char_name))
                self.update_status("已获取角色: {}".format(char_name))
            else:
                self.log("CurrentActor为空，尝试从场景中获取角色...")
                # 备用方法：从场景中获取角色
                scene = FBSystem().Scene
                if hasattr(scene, 'Characters') and hasattr(scene.Characters, '__len__'):
                    char_count = len(scene.Characters)
                    self.log("场景中角色数量: {}".format(char_count))
                    if char_count > 0:
                        char = scene.Characters[0]
                        char_name = char.Name
                        self.character_input.setText(char_name)
                        self.current_character = char_name
                        self.log("从场景获取角色: {}".format(char_name))
                        self.update_status("已获取角色: {}".format(char_name))
                    else:
                        self.character_input.setText("场景中无角色")
                        self.log("场景中没有找到任何角色")
                        self.update_status("场景中没有找到角色")
                else:
                    self.character_input.setText("无法获取角色")
                    self.log("无法访问场景角色列表")
                    self.update_status("无法访问场景角色")
                    
        except Exception as e:
            self.character_input.setText("获取角色失败")
            error_msg = "获取角色时出错: {}".format(str(e))
            self.log(error_msg)
            import traceback
            exc_info = traceback.format_exc()
            self.log("获取角色异常详情: {}".format(exc_info))
            self.update_status(error_msg)
            
    def select_source_path(self):
        """选择源数据路径"""
        path = QFileDialog.getExistingDirectory(self, "选择源数据目录")
        if path:
            self.source_path = path
            self.source_input.setText(path)
            self.update_status("已选择源数据目录: {}".format(path))
            
    def select_hik_path(self):
        """选择HIK文件路径"""
        path = QFileDialog.getExistingDirectory(self, "选择HIK文件目录")
        if path:
            self.hik_path = path
            self.hik_input.setText(path)
            self.update_status("已选择HIK文件目录: {}".format(path))
            
    def select_save_path(self):
        """选择保存路径"""
        path = QFileDialog.getExistingDirectory(self, "选择保存位置")
        if path:
            self.save_path = path
            self.save_input.setText(path)
            self.update_status("已选择保存位置: {}".format(path))
            
    def start_batch_process(self):
        """开始批处理"""
        self.log("=== 开始批处理配置检查 ===")
        
        # 验证输入
        if not self.source_path:
            self.log("错误：未选择源数据目录")
            QMessageBox.warning(self, "警告", "请选择源数据目录")
            return
            
        if not self.hik_path:
            self.log("错误：未选择HIK文件目录")
            QMessageBox.warning(self, "警告", "请选择HIK文件目录")
            return
            
        if not self.save_path:
            self.log("错误：未选择保存位置")
            QMessageBox.warning(self, "警告", "请选择保存位置")
            return
            
        if not self.current_character:
            self.log("错误：未获取当前场景角色")
            QMessageBox.warning(self, "警告", "请先获取当前场景角色")
            return
            
        if not os.path.exists(self.source_path):
            self.log("错误：源数据目录不存在: {}".format(self.source_path))
            QMessageBox.warning(self, "错误", "源数据目录不存在: {}".format(self.source_path))
            return
            
        if not os.path.exists(self.hik_path):
            self.log("错误：HIK文件目录不存在: {}".format(self.hik_path))
            QMessageBox.warning(self, "错误", "HIK文件目录不存在: {}".format(self.hik_path))
            return
            
        if not os.path.exists(self.save_path):
            self.log("错误：保存位置不存在: {}".format(self.save_path))
            QMessageBox.warning(self, "错误", "保存位置不存在: {}".format(self.save_path))
            return
        
        # 添加调试信息
        self.log("\n=== 批处理配置 ===")
        self.log("源数据目录: {}".format(self.source_path))
        self.log("HIK文件目录: {}".format(self.hik_path))
        self.log("保存位置: {}".format(self.save_path))
        self.log("当前角色: {}".format(self.current_character))
        
        # 检查MotionBuilder状态
        self.log("\n=== MotionBuilder状态 ===")
        try:
            system = FBSystem()
            scene = system.Scene
            self.log("场景组件数量: {}".format(len(scene.Components)))
            
            # 修复：使用FBApplication().CurrentCharacter
            character = FBApplication().CurrentCharacter
            if character:
                self.log("当前角色: {}".format(character.Name))
            else:
                self.log("当前角色: None")
                
            # 检查是否有Character在场景中
            characters = []
            for comp in scene.Components:
                if comp.ClassName() == 'FBCharacter':
                    characters.append(comp.Name)
            self.log("场景中的角色: {}".format(characters))
            
        except Exception as e:
            self.log("检查MotionBuilder状态时出错: {}".format(str(e)))
            import traceback
            exc_info = traceback.format_exc()
            self.log("MotionBuilder状态检查异常详情: {}".format(exc_info))
        
        # 快速检查是否能找到文件
        import glob
        source_fbx = glob.glob(os.path.join(self.source_path, "*.fbx"))
        hik_fbx = glob.glob(os.path.join(self.hik_path, "*.fbx"))
        self.log("\n=== 文件检查 ===")
        self.log("源目录FBX文件数量: {}".format(len(source_fbx)))
        self.log("HIK目录FBX文件数量: {}".format(len(hik_fbx)))
        
        if len(source_fbx) > 0:
            self.log("源文件示例: {}".format(source_fbx[0]))
        if len(hik_fbx) > 0:
            self.log("HIK文件示例: {}".format(hik_fbx[0]))
        
        # 启动批处理
        self.log("=== 准备启动批处理 ===")
        
        # 更新UI状态
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.update_status("开始批处理...")
        
        # 创建批处理器并运行
        self.batch_processor = BatchProcessor(self.source_path, self.hik_path, self.save_path, self.current_character, self.log_message)
        
        # 运行批处理
        success, message = self.batch_processor.run()
        
        # 批处理完成
        self.batch_finished(success, message)
        
    def stop_batch_process(self):
        """停止批处理"""
        if hasattr(self, 'batch_processor') and self.batch_processor:
            self.batch_processor.stop()
            self.batch_processor = None
            self.batch_finished(False, "批处理已停止")
            
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
        
    def update_status(self, message):
        """更新状态"""
        self.status_label.setText(message)
        self.log(message)
        
    def log(self, message):
        """统一的日志方法"""
        print(message)  # 输出到控制台
        self.log_message(message)  # 输出到UI日志
        
    def log_message(self, message):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = "[{}] {}".format(timestamp, message)
        self.log_text.append(log_entry)
        
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def batch_finished(self, success, message):
        """批处理完成"""
        self.log("=== 批处理结束回调 ===")
        self.log("成功: {}, 消息: {}".format(success, message))
        
        # 检查桌面Animation文件夹
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        animation_dir = os.path.join(desktop_path, "Animation")
        self.log("检查桌面Animation文件夹: {}".format(animation_dir))
        
        if os.path.exists(animation_dir):
            anim_files = [f for f in os.listdir(animation_dir) if f.lower().endswith('.fbx')]
            self.log("Animation文件夹中的FBX文件数量: {}".format(len(anim_files)))
            if anim_files:
                self.log("Animation文件夹中的文件:")
                for f in anim_files[:5]:  # 显示前5个
                    self.log("  - {}".format(f))
        else:
            self.log("Animation文件夹不存在")
        
        # 检查保存位置
        if hasattr(self, 'save_path') and self.save_path:
            self.log("检查保存位置: {}".format(self.save_path))
            if os.path.exists(self.save_path):
                save_files = [f for f in os.listdir(self.save_path) if f.lower().endswith('.fbx')]
                self.log("保存位置中的FBX文件数量: {}".format(len(save_files)))
                if save_files:
                    self.log("保存位置中的文件:")
                    for f in save_files[:5]:  # 显示前5个
                        self.log("  - {}".format(f))
            else:
                self.log("保存位置不存在")
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if success:
            self.log("批处理成功完成")
            self.update_status("批处理完成")
            QMessageBox.information(self, "完成", message)
        else:
            self.log("批处理失败: {}".format(message))
            self.update_status("批处理失败")
            QMessageBox.warning(self, "错误", message)


def show_animation_batch_ui():
    """显示动画批处理UI"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = AnimationReplaceBatchUI()
    window.show()
    
    return window

# 运行UI
if __name__ == "__main__":
    ui = show_animation_batch_ui()
else:
    # 在MotionBuilder中运行
    ui = show_animation_batch_ui() 