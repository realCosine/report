from pydantic import BaseModel, Field, field_validator, DirectoryPath, FilePath
from typing import Dict, List, Optional
from ...core_config import CoreConfig

class SpecificConfig(BaseModel):
    add_markets: Dict[str, str] = Field(default_factory=dict, description="Markets to add for specific report")
    remove_markets: List[str] = Field(default_factory=list, description="Markets to remove from specific report")

    @field_validator('remove_markets', mode='before')
    def check_remove_not_empty(cls, v):
        if not v:
            raise ValueError("Remove list cannot be empty")
        return v

class ReportConfig(BaseModel):
    generate_general: bool = Field(..., description="Flag to generate general report")
    generate_specific: bool = Field(..., description="Flag to generate specific report")
    specific: SpecificConfig = Field(..., description="Specific markets configuration")

    output_dir_general: Optional[DirectoryPath] = None
    output_dir_specific: Optional[DirectoryPath] = None

    @field_validator("output_dir_general", "output_dir_specific", mode='before')
    def check_suffix_not_empty(cls, v):
        if not v:
            raise ValueError("Output directory suffix cannot be empty")
        return v


class Config(BaseModel):
    core: CoreConfig = Field(..., description="Global configuration settings")
    report: ReportConfig = Field(..., description="Module-specific configuration settings")

    def prepare_dirs(self):
        import os
        
        base_dir = self.core.base_dir
        self.core.output_dir = base_dir / self.core.output_name
        self.core.is_dir = self.core.output_dir / self.core.is_file_name
        self.core.oos_dir = self.core.output_dir / self.core.oos_file_name

        self.report.output_dir_general = self.core.output_dir / "report"
        self.report.output_dir_specific = self.core.output_dir / "report_specific"

        if not os.path.exists(self.core.output_dir):
            os.makedirs(self.core.output_dir)

        if not os.path.exists(self.report.output_dir_general):
            os.makedirs(self.report.output_dir_general)
        
        if not os.path.exists(self.report.output_dir_specific):
            os.makedirs(self.report.output_dir_specific)
